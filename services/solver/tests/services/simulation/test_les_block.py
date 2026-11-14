"""Single block in the 3D LES: resolved gusts reach the Lawson gust factor.

An 18 m cube at dx = 2 m, wind from the west (flow toward +x). The
steady mixing-length model left ti ~ 0.1 everywhere and G = 1 on 97 %
of the window; the hybrid LES must resolve the wake unsteadiness.
"""

import numpy as np
import pytest

from app.models.jobs.payload_parser import parse_payload
from app.models.jobs.payload_schemas import HeavyPayload
from app.services.comfort.lawson_model import gust_factor
from app.services.device.array_module import to_host
from app.services.lbm3d.lbm3d_case import build_volume_case
from app.services.postprocess.output_fields import plan_output
from app.services.simulation.simulation_runner import SimulationRunner
from tests.support.gpu_marks import requires_gpu
from tests.support.scenario_factory import SceneBuilder, heavy_payload
from tests.support.stepper_choice import fastest

pytestmark = [pytest.mark.slow, pytest.mark.gpu, requires_gpu]
SCHEDULE = {"spinup_ft": 2.0, "min_avg_ft": 3.0, "max_avg_ft": 3.0, "check_every_ft": 0.25,
            "tolerance": 0.01, "consecutive": 3}
H = 18.0


@pytest.fixture(scope="module")
def block():
    scene = SceneBuilder().block("C", 0, 0, H, H, H).build()
    p = parse_payload(HeavyPayload, heavy_payload(scene, "volume3d", 270.0, 2.0, SCHEDULE))
    case = build_volume_case(p)
    stepper = fastest(case.problem)
    SimulationRunner(case, stepper, lambda *_: False).run()
    shape = case.problem.shape
    f = plan_output(case, to_host(stepper.avg_u).reshape((3,) + shape),
                    to_host(stepper.avg_u2).reshape(shape))
    stepper.close()
    g = p.grid.output
    gx, gy = np.meshgrid(g.origin_x + (np.arange(g.nx) + 0.5) * g.dx_m,
                         g.origin_y + (np.arange(g.ny) + 0.5) * g.dx_m)
    return f.arrays, gx, gy


def _zone(block, x0, x1, y0, y1, name):
    arrays, gx, gy = block
    sel = (gx >= x0) & (gx <= x1) & (gy >= y0) & (gy <= y1) & np.isfinite(arrays[name])
    return arrays[name][sel]


def test_far_field_beside_the_block_keeps_k_near_one(block) -> None:
    k = np.concatenate([_zone(block, -2 * H, 3 * H, -3 * H, -2 * H, "K"),
                        _zone(block, -2 * H, 3 * H, 3 * H, 4 * H, "K")])
    print(f"lateral far field K = {k.mean():.3f}")
    assert 0.9 <= k.mean() <= 1.1


def test_wake_is_more_turbulent_than_the_far_field(block) -> None:
    wake = _zone(block, H, 2.5 * H, 0, H, "ti").mean()
    far = np.concatenate([_zone(block, -2 * H, 3 * H, -3 * H, -2 * H, "ti"),
                          _zone(block, -2 * H, 3 * H, 3 * H, 4 * H, "ti")]).mean()
    print(f"ti wake {wake:.3f} vs far field {far:.3f}")
    assert far >= 0.10
    assert wake >= 1.5 * far


def test_lawson_gust_factor_leaves_its_floor(block) -> None:
    arrays, _, _ = block
    g = gust_factor(arrays["ti"][np.isfinite(arrays["ti"])])
    share = float((g > 1.0).mean())
    print(f"G > 1 on {100 * share:.1f} % of the window, G max {g.max():.2f}")
    assert share >= 0.05


def test_corner_streams_still_accelerate(block) -> None:
    corners = np.concatenate([_zone(block, -0.5 * H, 1.5 * H, H, 2 * H, "K"),
                              _zone(block, -0.5 * H, 1.5 * H, -H, 0, "K")])
    print(f"corner K max {corners.max():.3f}")
    assert corners.max() >= 1.2
