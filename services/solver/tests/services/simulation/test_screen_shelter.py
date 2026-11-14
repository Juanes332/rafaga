"""A porosity-0.40 screen shelters the zone behind it, in 2D (fast) and 3D (gpu) (BL-03).

A block with and without a screen on its windward edge, perpendicular to the wind (from the
west, flow toward +x). The screen overhangs the block laterally, so the zone downstream of the
overhang (within 3 screen heights, at z_a) is not hidden in the block's own wake. The zone and
the threshold are module constants, not tuned per run.
"""

import numpy as np
import pytest

from app.models.jobs.payload_parser import parse_payload
from app.models.jobs.payload_schemas import HeavyPayload
from app.services.device.array_module import to_host
from app.services.lbm2d.lbm2d_case import build_plan_case
from app.services.lbm3d.lbm3d_case import build_volume_case
from app.services.postprocess.output_fields import plan_output
from app.services.simulation.heavy_job_service import make_stepper
from app.services.simulation.simulation_runner import SimulationRunner
from tests.support.gpu_marks import requires_gpu
from tests.support.scenario_factory import SceneBuilder, heavy_payload

POROSITY = 0.40
SCREEN_HEIGHT_M = 4.0
SHELTER_LENGTH_SCREEN_HEIGHTS = 3.0  # zone: 3 screen heights downstream of the screen
MIN_K_REDUCTION = 0.10
BLOCK = (0.0, 0.0, 12.0, 24.0, 8.0)  # x0, y0, x1, y1, height
SCREEN_OVERHANG_M = 6.0  # screen extends this far past each lateral face of the block
SCREEN_THICKNESS_M = 3.0  # one cell at the 2D resolution
DX_2D_M, DX_3D_M = 3.0, 1.0
SCHEDULE = {"spinup_ft": 1.5, "min_avg_ft": 1.0, "max_avg_ft": 2.0, "check_every_ft": 0.25,
            "tolerance": 0.01, "consecutive": 3}
SCHEDULE_2D = {"spinup_ft": 1.0, "min_avg_ft": 0.5, "max_avg_ft": 1.0, "check_every_ft": 0.25,
               "tolerance": 0.01, "consecutive": 3}


def _scene(with_screen: bool) -> SceneBuilder:
    builder = SceneBuilder().block("T", *BLOCK)
    if with_screen:
        builder.screen("s", -SCREEN_THICKNESS_M, BLOCK[1] - SCREEN_OVERHANG_M, 0.0,
                       BLOCK[3] + SCREEN_OVERHANG_M, SCREEN_HEIGHT_M, (-1.0, 0.0), porosity=POROSITY)
    return builder


def _mean_k_in_shelter(with_screen: bool, kind: str, dx: float, device: str,
                       schedule: dict = SCHEDULE) -> float:
    """Run the case and return mean K at z_a downstream of the screen."""
    raw = heavy_payload(_scene(with_screen).build(), kind, 270.0, dx, schedule, device)
    p = parse_payload(HeavyPayload, raw)
    case = (build_volume_case if kind == "volume3d" else build_plan_case)(p)
    stepper = make_stepper(case.problem, device)
    SimulationRunner(case, stepper, lambda *_: False).run()
    shape = case.problem.shape
    f = plan_output(case, to_host(stepper.avg_u).reshape((-1,) + shape),
                    to_host(stepper.avg_u2).reshape(shape))
    stepper.close()
    g = p.grid.output
    gx, gy = np.meshgrid(g.origin_x + (np.arange(g.nx) + 0.5) * g.dx_m,
                         g.origin_y + (np.arange(g.ny) + 0.5) * g.dx_m)
    x_end = SHELTER_LENGTH_SCREEN_HEIGHTS * SCREEN_HEIGHT_M  # screen downstream face is x = 0
    beside = (gy < BLOCK[1]) | (gy > BLOCK[3])
    zone = (gx >= 0.0) & (gx <= x_end) & beside & (gy >= BLOCK[1] - SCREEN_OVERHANG_M) \
        & (gy <= BLOCK[3] + SCREEN_OVERHANG_M)
    k = f.arrays["K"]
    return float(k[zone & np.isfinite(k)].mean())


def test_windward_screen_reduces_sheltered_k_in_2d() -> None:
    bare = _mean_k_in_shelter(False, "plan2d", DX_2D_M, "cpu", SCHEDULE_2D)
    screened = _mean_k_in_shelter(True, "plan2d", DX_2D_M, "cpu", SCHEDULE_2D)
    print(f"2D sheltered K {bare:.3f} -> {screened:.3f}")
    assert screened <= (1.0 - MIN_K_REDUCTION) * bare


@pytest.mark.slow
@pytest.mark.gpu
@requires_gpu
def test_windward_screen_reduces_sheltered_k_in_3d() -> None:
    bare = _mean_k_in_shelter(False, "volume3d", DX_3D_M, "gpu")
    screened = _mean_k_in_shelter(True, "volume3d", DX_3D_M, "gpu")
    print(f"3D sheltered K {bare:.3f} -> {screened:.3f}")
    assert screened <= (1.0 - MIN_K_REDUCTION) * bare
