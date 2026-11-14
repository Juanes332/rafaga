"""Runner guards and progress (ADR-11, ADR-14)."""

import numpy as np
import pytest

from app.core.errors.solver_errors import JobCancelledError, NumericalInstabilityError
from app.models.jobs.payload_parser import parse_payload
from app.models.jobs.payload_schemas import HeavyPayload
from app.services.lattice.numpy_stepper import CpuStepper
from app.services.lbm2d.lbm2d_case import build_plan_case
from app.services.simulation.simulation_runner import SimulationRunner
from tests.support.payload_factory import plan_payload


def _case():
    return build_plan_case(parse_payload(HeavyPayload, plan_payload(dx=8.0, device="cpu")))


def test_progress_is_monotonic_and_run_completes() -> None:
    case = _case()
    seen = []
    outcome = SimulationRunner(case, CpuStepper(case.problem, 2),
                               lambda p, ph, eta: seen.append(p) or False).run()
    assert seen == sorted(seen) and outcome.steps > 0
    assert outcome.monitor.checks >= 1


def test_cancel_flag_stops_the_run() -> None:
    case = _case()
    with pytest.raises(JobCancelledError):
        SimulationRunner(case, CpuStepper(case.problem, 2), lambda *_: True).run()


def test_nan_triggers_numerical_instability() -> None:
    case = _case()
    stepper = CpuStepper(case.problem, 2)
    stepper.f[:, 5] = np.nan
    with pytest.raises(NumericalInstabilityError) as err:
        SimulationRunner(case, stepper, lambda *_: False).run()
    assert "step" in err.value.details


class _SpikyStepper:
    """Wrap a stepper and fake a local velocity spike on chosen guards."""

    def __init__(self, inner, spikes: set[int]) -> None:
        self.inner, self.spikes, self.calls = inner, spikes, 0
        self.xp, self.problem = inner.xp, inner.problem

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def step(self, n, accumulate=False):
        self.inner.step(n, accumulate)

    def macroscopic(self):
        rho, u = self.inner.macroscopic()
        self.calls += 1
        if self.calls in self.spikes:
            u = u.copy()
            u[0, int(self.inner.problem.mask.reshape(-1).argmin())] = 0.25
        return rho, u


def test_isolated_mach_spike_is_tolerated_and_reported() -> None:
    case = _case()
    stepper = _SpikyStepper(CpuStepper(case.problem, 2), {2})
    outcome = SimulationRunner(case, stepper, lambda *_: False).run()
    assert outcome.mach_spikes == 1


def test_persistent_mach_excess_fails() -> None:
    case = _case()
    stepper = _SpikyStepper(CpuStepper(case.problem, 2), {2, 3, 4})
    with pytest.raises(NumericalInstabilityError):
        SimulationRunner(case, stepper, lambda *_: False).run()
