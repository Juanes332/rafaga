"""volume3d case: hybrid RANS/LES closure, turbulent inflow and nudging."""

import numpy as np
import pytest

from app.models.jobs.payload_parser import parse_payload
from app.models.jobs.payload_schemas import HeavyPayload
from app.services.boundary.abl_closure import RANS_LAYERS
from app.services.boundary.inflow_turbulence import FRAME_STEPS, MIN_FRAMES
from app.services.lbm3d.lbm3d_case import build_volume_case
from tests.support.scenario_factory import SceneBuilder, heavy_payload


@pytest.fixture(scope="module")
def case():
    scene = SceneBuilder().block("A", 0, 0, 20, 20, 12).build()
    return build_volume_case(parse_payload(HeavyPayload, heavy_payload(scene, "volume3d", dx=4.0)))


def test_volume_case_is_les_above_the_rans_layer(case) -> None:
    lm = case.problem.mixing_length
    cs = np.float32(case.payload.physics.smagorinsky_cs)
    assert np.all(lm[RANS_LAYERS:] == cs)
    assert lm[: RANS_LAYERS].max() > 10 * cs


def test_volume_case_has_a_correlated_turbulent_inflow_bank(case) -> None:
    p = case.problem
    nz, ny, _ = p.shape
    assert p.inlet.shape[0] >= MIN_FRAMES and p.inlet.shape[1:] == (3, nz * ny)
    assert p.inlet_period == FRAME_STEPS
    u = p.inlet[:, 0].reshape(-1, nz, ny)
    iu = u.std(axis=(0, 2)) / u.mean(axis=(0, 2))
    assert 0.15 <= iu[0] <= 0.30


def test_volume_case_nudges_the_far_field_to_the_inlet_profile(case) -> None:
    p = case.problem
    assert p.nudge is not None
    nz, ny, _ = p.shape
    assert np.allclose(p.nudge.target, p.inlet[:, 0].reshape(-1, nz, ny).mean(axis=(0, 2)), rtol=1e-3)


def test_zero_perturbation_keeps_a_steady_log_inflow() -> None:
    scene = SceneBuilder().block("A", 0, 0, 20, 20, 12).build()
    raw = heavy_payload(scene, "volume3d", dx=4.0)
    raw["physics"]["inflow_perturbation"] = 0.0
    p = build_volume_case(parse_payload(HeavyPayload, raw)).problem
    assert p.inlet.shape[0] == 1
