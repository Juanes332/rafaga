"""Time loop: spin-up, averaging, checks, guards, progress (ADR-11, ADR-14)."""

import math
import time
from collections.abc import Callable
from dataclasses import dataclass


import numpy as np

from app.core.errors.solver_errors import JobCancelledError, NumericalInstabilityError
from app.services.convergence.convergence_monitor import ConvergenceMonitor
from app.services.device.array_module import to_host
from app.services.lattice.lattice_problem import SOLID
from app.services.lattice.lattice_units import flow_through_steps
from app.services.simulation.simulation_case import SimulationCase

# progress (0..1), phase, eta seconds -> True when cancellation was asked.
Reporter = Callable[[float, str, int | None], bool]
_GUARD_EVERY = 100
_TARGET_CHUNK_S = 0.5
_PERSIST = 3


@dataclass
class RunOutcome:
    """What the loop produced besides the stepper's averages."""

    monitor: ConvergenceMonitor
    steps: int
    averaged_steps: int
    wall_s: float
    mlups: float
    mach_spikes: int = 0


class SimulationRunner:
    """Drive a stepper through the ADR-11 schedule."""

    def __init__(self, case: SimulationCase, stepper, reporter: Reporter) -> None:
        """Bind case, stepper and progress/cancel callback."""
        self.case = case
        self.stepper = stepper
        self.reporter = reporter
        ft = flow_through_steps(case.problem.nx, case.units.u_lat)
        self.monitor = ConvergenceMonitor(case.payload.convergence, ft,
                                         fixed_length=case.kind == "plan2d")
        self.fluid = stepper.xp.asarray(case.problem.mask.reshape(-1) != SOLID)
        self.chunk = _GUARD_EVERY
        self.progress = 0.0
        self.mlups = 0.0
        self.mach_streak = 0
        self.mach_spikes = 0

    def run(self) -> RunOutcome:
        """Run until converged or capped; return the outcome."""
        start = time.perf_counter()
        mon = self.monitor
        self._advance(mon.spinup_steps, False, "spinup", 0)
        averaged = 0
        while True:
            self._advance(mon.check_steps, True, "averaging", averaged)
            averaged += mon.check_steps
            if mon.check(self._window_speed(), averaged):
                break
        wall = time.perf_counter() - start
        steps = mon.spinup_steps + averaged
        rate = self.case.problem.nodes * steps / max(wall, 1e-9) / 1e6
        return RunOutcome(mon, steps, averaged, wall, rate, self.mach_spikes)

    def _advance(self, n_steps: int, accumulate: bool, phase: str, averaged: int) -> None:
        """Step n_steps in timed chunks, guarding and reporting between them."""
        done = 0
        while done < n_steps:
            todo = min(self.chunk, n_steps - done)
            tic = time.perf_counter()
            self.stepper.step(todo, accumulate)
            self._sync()
            elapsed = max(time.perf_counter() - tic, 1e-6)
            self._tune(todo, elapsed)
            done += todo
            if self.stepper.t % _GUARD_EVERY < todo or done == n_steps:
                self._guard()
            self._report(phase, averaged + (done if accumulate else 0))

    def _sync(self) -> None:
        """Wait for the device so timings are real."""
        sync = getattr(self.stepper, "synchronize", None)
        if sync:
            sync()

    def _tune(self, steps: int, elapsed: float) -> None:
        """Adapt the chunk so a report happens about twice per second."""
        self.mlups = self.case.problem.nodes * steps / elapsed / 1e6
        ideal = steps * _TARGET_CHUNK_S / elapsed
        self.chunk = max(_GUARD_EVERY, int(ideal // _GUARD_EVERY) * _GUARD_EVERY)

    def _guard(self) -> None:
        """Abort on NaN, or on local Mach above the limit that persists.

        2D plan wakes concentrate vortices into grid-sized cores whose
        swirl briefly crosses Ma 0.35 at a single check; divergence
        persists and grows. NaN, Mach > 2x the limit, or the limit
        exceeded on _PERSIST consecutive checks (300 steps) fail the job.
        """
        xp = self.stepper.xp
        rho, u = self.stepper.macroscopic()
        speed = xp.where(self.fluid, xp.sqrt((u * u).sum(axis=0)), 0)
        finite = bool(xp.isfinite(xp.where(self.fluid, rho, 1)).all())
        max_mach = float(speed.max()) * math.sqrt(3.0) if finite else float("nan")
        limit = self.case.payload.physics.max_local_mach
        over = finite and math.isfinite(max_mach) and max_mach > limit
        self.mach_streak = self.mach_streak + 1 if over else 0
        self.mach_spikes += int(over)
        if not finite or not math.isfinite(max_mach) or max_mach > 2 * limit \
                or self.mach_streak >= _PERSIST:
            raise NumericalInstabilityError(
                "lattice diverged",
                {"step": int(self.stepper.t),
                 "max_mach": round(max_mach, 4) if math.isfinite(max_mach) else None},
            )

    def _report(self, phase: str, averaged: int) -> None:
        """Publish monotonic progress and ETA; stop when cancelled."""
        planned = self.monitor.planned_steps(averaged)
        self.progress = max(self.progress, min(self.stepper.t / planned, 0.99))
        remaining = max(planned - self.stepper.t, 0)
        eta = int(remaining * self.case.problem.nodes / max(self.mlups * 1e6, 1.0))
        if self.reporter(self.progress, phase, eta):
            raise JobCancelledError()

    def _window_speed(self) -> np.ndarray:
        """Return the mean-speed magnitude on the convergence window."""
        avg = self.stepper.avg_u[:, self.case.window]
        return to_host(self.stepper.xp.sqrt((avg * avg).sum(axis=0)))
