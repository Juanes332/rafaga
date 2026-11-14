"""Synthetic turbulent inflow: target statistics, correlation and size."""

import numpy as np
import pytest

from app.services.boundary.inflow_turbulence import (
    INFLOW_IU_CAP,
    InflowSpec,
    target_stresses,
    turbulent_inlet_bank,
)
from app.services.boundary.log_profile import lattice_inlet_profile

KAPPA = 0.41
NZ, NY, DX, Z0, U_LAT = 24, 40, 2.0, 1.0, 0.05


def _spec(**kw) -> InflowSpec:
    profile = lattice_inlet_profile(NZ, DX, Z0, U_LAT)
    ustar = KAPPA * U_LAT / np.log((NZ * DX + Z0) / Z0)
    base = {"profile": profile, "ny": NY, "ustar": float(ustar), "length_cells": 8.0,
            "seed": 7, "frames": 256}
    return InflowSpec(**(base | kw))


def _bank(**kw) -> tuple[np.ndarray, InflowSpec]:
    spec = _spec(**kw)
    return turbulent_inlet_bank(spec), spec


def test_bank_is_float32_frames_by_components_by_rows() -> None:
    bank, _ = _bank()
    assert bank.dtype == np.float32
    assert bank.shape == (256, 3, NZ * NY)


def test_bank_is_deterministic_for_a_seed_and_differs_across_seeds() -> None:
    a, _ = _bank()
    b, _ = _bank()
    c, _ = _bank(seed=8)
    assert np.array_equal(a, b)
    assert not np.allclose(a, c)


def test_mean_of_every_level_is_the_log_profile() -> None:
    bank, spec = _bank()
    u = bank[:, 0].reshape(-1, NZ, NY).mean(axis=(0, 2))
    assert np.allclose(u, spec.profile, atol=1e-4)
    assert np.abs(bank[:, 1:].mean()) < 1e-4


def test_streamwise_intensity_follows_the_capped_neutral_abl() -> None:
    bank, spec = _bank()
    su, sv, sw, _ = target_stresses(spec.profile, spec.ustar)
    sigma = bank[:, 0].reshape(-1, NZ, NY).std(axis=(0, 2))
    assert np.allclose(sigma, su, rtol=0.02)
    assert np.all(su / spec.profile <= INFLOW_IU_CAP + 1e-6)
    assert su[-1] == pytest.approx(min(2.5 * spec.ustar, INFLOW_IU_CAP * spec.profile[-1]))
    assert np.all(sv < su) and np.all(sw < sv)


def test_shear_stress_is_negative_and_bounded_by_ustar_squared() -> None:
    bank, spec = _bank()
    u = bank[:, 0].reshape(-1, NZ, NY) - spec.profile[None, :, None]
    w = bank[:, 2].reshape(-1, NZ, NY)
    uw = (u * w).mean(axis=(0, 2))
    _, _, _, target = target_stresses(spec.profile, spec.ustar)
    assert np.all(uw < 0)
    assert np.allclose(uw, target, rtol=0.1, atol=0.05 * spec.ustar**2)
    assert np.all(-target <= spec.ustar**2 * (1 + 1e-6))


def test_consecutive_frames_are_strongly_correlated() -> None:
    bank, spec = _bank()
    fluct = bank[:, 0] - np.repeat(spec.profile, NY)[None]
    lag1 = (fluct[1:] * fluct[:-1]).mean() / (fluct * fluct).mean()
    far = (fluct[64:] * fluct[:-64]).mean() / (fluct * fluct).mean()
    assert lag1 > 0.95
    assert abs(far) < 0.3


def test_frame_count_respects_the_byte_budget() -> None:
    spec = _spec(frames=None, max_bytes=3 * NZ * NY * 4 * 100)
    assert turbulent_inlet_bank(spec).shape[0] == 100
