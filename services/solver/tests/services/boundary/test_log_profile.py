"""Tests for the shifted log law and inlet helpers."""

import numpy as np
import pytest

from app.services.boundary.log_profile import (
    friction_velocity, lattice_inlet_profile, log_speed, perturbation_bank,
    sponge_ramp, wall_drag_coefficient,
)


def test_contract_example_ustar_and_uref() -> None:
    ustar = friction_velocity(10.0, 1.0)
    assert ustar == pytest.approx(1.7098, abs=1e-4)
    assert float(log_speed(1.5, ustar, 1.0)) == pytest.approx(3.8212, abs=1e-4)


def test_shifted_law_is_positive_when_z0_exceeds_za() -> None:
    assert float(log_speed(1.5, friction_velocity(10, 2.0), 2.0)) > 0
    assert float(log_speed(0.0, 1.0, 1.0)) == 0.0


def test_inlet_profile_reaches_u_lat_at_top_and_grows() -> None:
    prof = lattice_inlet_profile(40, 1.0, 1.0, 0.05)
    assert np.all(np.diff(prof) > 0)
    assert prof[-1] < 0.05 and prof[-1] == pytest.approx(0.05, rel=0.01)


def test_sponge_ramp_spans_last_tenth() -> None:
    ramp = sponge_ramp(100, 0.1)
    assert ramp[:90].max() == 0 and ramp[-1] == 1


def test_perturbation_bank_is_seeded_and_bounded() -> None:
    base = np.full((3, 10), 0.05, dtype=np.float32)
    a, b = perturbation_bank(base, 0.02, 7), perturbation_bank(base, 0.02, 7)
    assert np.array_equal(a, b)
    assert np.abs(a - base).max() <= 0.02 * 0.05 + 1e-7


def test_wall_drag_coefficient_positive() -> None:
    assert wall_drag_coefficient(1.0, 1.0) == pytest.approx((0.41 / np.log(1.5)) ** 2)
