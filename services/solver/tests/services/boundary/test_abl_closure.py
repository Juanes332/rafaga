"""Equilibrium ABL closure: mixing length, top shear and matched wall drag."""

import numpy as np
import pytest

from app.models.jobs.payload_parser import parse_payload
from app.models.jobs.payload_schemas import HeavyPayload
from app.services.boundary.abl_closure import mixing_length_field, top_shear_stress
from app.services.boundary.log_profile import (
    lattice_inlet_profile,
    wall_drag_coefficient,
)
from app.services.lbm3d.lbm3d_case import build_volume_case
from tests.support.scenario_factory import SceneBuilder, heavy_payload

KAPPA = 0.41


def test_mixing_length_is_kappa_z_plus_z0_in_free_column() -> None:
    mask = np.zeros((10, 6, 8), dtype=np.uint8)
    lm = mixing_length_field(mask, dx=2.0, z0=1.0, floor=0.17)
    z = (np.arange(10) + 0.5) * 2.0
    assert np.allclose(lm[:, 3, 4], KAPPA * (z + 1.0) / 2.0, rtol=1e-5)


def test_mixing_length_is_limited_by_building_walls_and_floored() -> None:
    mask = np.zeros((12, 9, 9), dtype=np.uint8)
    mask[:, 4, 4] = 1
    lm = mixing_length_field(mask, dx=1.0, z0=0.01, floor=0.17)
    assert lm[8, 4, 5] == pytest.approx(KAPPA * 0.5, rel=1e-5)
    assert lm[8, 4, 5] < lm[8, 0, 0]
    assert lm.min() >= 0.17


def test_top_shear_equals_wall_drag_of_the_inlet_profile() -> None:
    nz, dx, z0, u = 40, 2.0, 1.0, 0.05
    prof = lattice_inlet_profile(nz, dx, z0, u)
    tau_wall = wall_drag_coefficient(dx, z0) * prof[0] ** 2
    assert top_shear_stress(nz, dx, z0, u) == pytest.approx(tau_wall, rel=1e-4)


def test_volume_case_has_slip_ground_top_shear_and_mixing_length() -> None:
    scene = SceneBuilder().block("A", 0, 0, 20, 20, 12).build()
    case = build_volume_case(parse_payload(HeavyPayload, heavy_payload(scene, "volume3d", dx=4.0)))
    p = case.problem
    assert p.ground_slip and p.top_force > 0
    assert p.mixing_length is not None and p.mixing_length.shape == p.shape


def test_hybrid_length_is_damped_mixing_length_below_the_interface_and_les_above() -> None:
    from app.services.boundary.abl_closure import (
        RANS_FACTOR,
        RANS_LAYERS,
        hybrid_length_field,
    )

    mask = np.zeros((16, 6, 8), dtype=np.uint8)
    lm = hybrid_length_field(mask, dx=2.0, z0=1.0, cs=0.17)
    full = mixing_length_field(mask, dx=2.0, z0=1.0, floor=0.17)
    below = slice(0, RANS_LAYERS)
    assert np.allclose(lm[below], np.maximum(RANS_FACTOR * full[below], 0.17), rtol=1e-6)
    assert np.all(lm[RANS_LAYERS:] == np.float32(0.17))
    assert lm.dtype == np.float32
