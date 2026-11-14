"""Screen pressure loss in a 2D channel within 15 % of zeta * rho u^2 / 2 (ADR-13)."""

import numpy as np
import pytest

from app.services.bench.validation_cases import porous_channel
from app.services.device.array_module import to_host
from tests.support.stepper_choice import fastest


def _pressure_ratio(beta: float) -> float:
    problem, geo = porous_channel(beta, nx=160)
    stepper = fastest(problem)
    stepper.step(24000)
    rho, u = (to_host(a) for a in stepper.macroscopic())
    rho, ux = rho.reshape(problem.shape), u[0].reshape(problem.shape)
    xs = geo["x_screen"]
    dp = (rho[:, xs - 40 : xs - 10].mean() - rho[:, xs + 10 : xs + 40].mean()) / 3.0
    un = ux[:, xs + 20].mean()
    return float(dp / (geo["zeta"] * 0.5 * un * un))


@pytest.mark.parametrize("beta", [0.2, 0.4, 0.6])
def test_screen_loss_matches_idelchik(beta) -> None:
    assert _pressure_ratio(beta) == pytest.approx(1.0, abs=0.15)


def test_lowest_porosity_stays_stable() -> None:
    problem, _ = porous_channel(0.05, nx=160)
    stepper = fastest(problem)
    stepper.step(6000)
    assert np.isfinite(to_host(stepper.f)).all()
