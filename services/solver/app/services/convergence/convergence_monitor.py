"""Spin-up, running average and convergence checks (ADR-11, SOL-10)."""

import math
from dataclasses import dataclass, field

import numpy as np

from app.models.jobs.payload_schemas import ConvergenceParams


@dataclass
class ConvergenceMonitor:
    """Decide when averaging may stop; all times in lattice steps.

    With `fixed_length` (plan2d) every run averages exactly max_avg_ft:
    2D wakes shed vortices whose cumulative mean creeps under the 1 %
    tolerance anywhere between 4 and 8 FT, so comparable runs (base vs
    alternative) ended up averaged over different windows and some hit
    the cap. A common window makes their difference meaningful; the
    ADR-11 test is still evaluated and reported at the end.
    """

    params: ConvergenceParams
    ft_steps: int
    fixed_length: bool = False
    checks: int = 0
    passes: int = 0
    rel_change_last: float | None = None
    mean_change_last: float | None = None
    converged: bool = False
    cap_reached: bool = False
    _previous: np.ndarray | None = field(default=None, repr=False)

    @property
    def spinup_steps(self) -> int:
        """Return the unaveraged spin-up length."""
        return round(self.params.spinup_ft * self.ft_steps)

    @property
    def check_steps(self) -> int:
        """Return the averaging steps between two checks."""
        return max(1, round(self.params.check_every_ft * self.ft_steps))

    @property
    def min_avg_steps(self) -> int:
        """Return the minimum averaging length."""
        return round(self.params.min_avg_ft * self.ft_steps)

    @property
    def max_avg_steps(self) -> int:
        """Return the averaging cap."""
        return round(self.params.max_avg_ft * self.ft_steps)

    def check(self, mean_speed: np.ndarray, averaged_steps: int) -> bool:
        """Record one check of the windowed mean speed; return True to stop."""
        self.checks += 1
        current = np.asarray(mean_speed, dtype=np.float64)
        if self._previous is not None:
            norm = float(np.linalg.norm(current)) or 1.0
            self.rel_change_last = float(np.linalg.norm(current - self._previous)) / norm
            mean = float(current.mean()) or 1.0
            self.mean_change_last = abs(mean - float(self._previous.mean())) / abs(mean)
            ok = max(self.rel_change_last, self.mean_change_last) < self.params.tolerance
            self.passes = self.passes + 1 if ok else 0
        self._previous = current
        stable = self.passes >= self.params.consecutive
        if self.fixed_length:
            if averaged_steps >= self.max_avg_steps:
                self.converged, self.cap_reached = stable, not stable
            return averaged_steps >= self.max_avg_steps
        if averaged_steps >= self.min_avg_steps and stable:
            self.converged = True
        elif averaged_steps >= self.max_avg_steps:
            self.cap_reached = True
        return self.converged or self.cap_reached

    def planned_steps(self, averaged_steps: int) -> int:
        """Return the planned total steps (job-contract.md section 4)."""
        if self.fixed_length:
            return self.spinup_steps + self.max_avg_steps
        base = self.spinup_steps + self.min_avg_steps
        if averaged_steps < self.min_avg_steps:
            return base
        extended = self.spinup_steps + averaged_steps + self.check_steps
        return min(extended, self.spinup_steps + self.max_avg_steps)

    def report(self, averaged_steps: int) -> dict:
        """Return manifest.convergence (contract section 6 + SOL-10 names)."""
        averaged_ft = averaged_steps / self.ft_steps
        rel = _rounded(self.rel_change_last)
        return {
            "converged": self.converged,
            "flow_through_steps": self.ft_steps,
            "spinup_ft": self.params.spinup_ft,
            "averaged_ft": round(averaged_ft, 4),
            "checks": self.checks,
            "rel_change_last": rel,
            "mean_speed_change_last": _rounded(self.mean_change_last),
            "cap_reached": self.cap_reached,
            "flow_throughs_spinup": self.params.spinup_ft,
            "flow_throughs_averaged": round(averaged_ft, 4),
            "averaging": "fixed" if self.fixed_length else "adaptive",
        }


def _rounded(value: float | None) -> float | None:
    """Return value rounded for the manifest, keeping None and NaN out."""
    if value is None or not math.isfinite(value):
        return None
    return round(value, 6)
