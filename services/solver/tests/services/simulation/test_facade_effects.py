"""Facade strategies change K where physics says they should (item: US-13 credibility).

Single tall block, wind from the west (flow toward +x). 3D runs on the GPU.
"""

import numpy as np
import pytest

from app.models.jobs.payload_parser import parse_payload
from app.models.jobs.payload_schemas import HeavyPayload
from app.services.device.array_module import to_host
from app.services.lbm2d.lbm2d_case import build_plan_case
from app.services.lbm3d.lbm3d_case import build_volume_case
from app.services.postprocess.output_fields import plan_output
from app.services.simulation.simulation_runner import SimulationRunner
from tests.support.gpu_marks import requires_gpu
from tests.support.scenario_factory import SceneBuilder, heavy_payload
from tests.support.stepper_choice import fastest

pytestmark = [pytest.mark.slow, pytest.mark.gpu, requires_gpu]
SCHEDULE = {"spinup_ft": 1.5, "min_avg_ft": 1.0, "max_avg_ft": 2.0, "check_every_ft": 0.25,
            "tolerance": 0.01, "consecutive": 3}
DX = 2.5


def _k(builder: SceneBuilder, kind: str = "volume3d", dx: float = DX):
    """Return (K, east centres, north centres) at z_a."""
    p = parse_payload(HeavyPayload, heavy_payload(builder.build(), kind, 270.0, dx, SCHEDULE))
    case = (build_volume_case if kind == "volume3d" else build_plan_case)(p)
    stepper = fastest(case.problem)
    SimulationRunner(case, stepper, lambda *_: False).run()
    shape = case.problem.shape
    f = plan_output(case, to_host(stepper.avg_u).reshape((-1,) + shape),
                    to_host(stepper.avg_u2).reshape(shape))
    stepper.close()
    g = p.grid.output
    return (f.arrays["K"], g.origin_x + (np.arange(g.nx) + 0.5) * g.dx_m,
            g.origin_y + (np.arange(g.ny) + 0.5) * g.dx_m)


def _mean(field, x0, x1, y0, y1) -> float:
    k, xs, ys = field
    gx, gy = np.meshgrid(xs, ys)
    sel = (gx >= x0) & (gx <= x1) & (gy >= y0) & (gy <= y1) & np.isfinite(k)
    return float(k[sel].mean())


def _tower() -> SceneBuilder:
    return SceneBuilder().block("T", 0, 0, 16, 24, 30)


@pytest.fixture(scope="module")
def tower_base():
    return _k(_tower())


def test_canopy_shelters_the_windward_base(tower_base) -> None:
    canopy = _k(_tower().canopy("c", -3, 0, 0, 24, 4.0))
    before, after = _mean(tower_base, -6, 0, 0, 24), _mean(canopy, -6, 0, 0, 24)
    print(f"windward base K {before:.3f} -> {after:.3f}")
    assert after <= 0.95 * before


def test_corner_fins_slow_the_corner_stream(tower_base) -> None:
    fins = _tower()
    for x in (0.0, 4.0):
        fins.fin("f", x, 24, x + 0.3, 27, 30).fin("f", x, -3, x + 0.3, 0, 30)
    with_fins = _k(fins)
    before = _mean(tower_base, -2, 16, 24, 30) + _mean(tower_base, -2, 16, -6, 0)
    after = _mean(with_fins, -2, 16, 24, 30) + _mean(with_fins, -2, 16, -6, 0)
    print(f"corner K {before / 2:.3f} -> {after / 2:.3f}")
    assert after <= 0.92 * before


def _pair() -> SceneBuilder:
    return SceneBuilder().block("A", 0, 0, 30, 12, 24).block("B", 0, 20, 30, 32, 24)


def _screened() -> SceneBuilder:
    return _pair().screen("s", -0.1, 12, 0.0, 20, 24, (-1.0, 0.0))


def test_screen_across_a_passage_slows_it_in_3d() -> None:
    before, after = _mean(_k(_pair()), 0, 30, 12, 20), _mean(_k(_screened()), 0, 30, 12, 20)
    print(f"3D passage K {before:.3f} -> {after:.3f}")
    # Mixing-length model: 0.850 -> 0.596 (-30 %). Hybrid LES: the open
    # passage is already slower (0.60) and the screen takes ~12 % more.
    assert after <= 0.9 * before


def test_screen_across_a_passage_gives_negative_delta_k_in_2d() -> None:
    base, screen = _k(_pair(), "plan2d", 1.0), _k(_screened(), "plan2d", 1.0)
    delta = screen[0] - base[0]
    k, xs, ys = base
    gx, gy = np.meshgrid(xs, ys)
    passage = (gx >= 0) & (gx <= 30) & (gy >= 12) & (gy <= 20) & np.isfinite(delta)
    print(f"2D passage mean dK {delta[passage].mean():.3f}")
    assert delta[passage].mean() < -0.1


def _free_screen(orientation: str | None) -> SceneBuilder:
    """Return a 3 m tall, 30 m long celosia alone in the open (H = 6 m domain)."""
    b = SceneBuilder()
    if orientation == "perpendicular":
        b.screen("s", 0.0, -15, 0.1, 15, 3.0, (-1.0, 0.0))
    elif orientation == "parallel":
        b.screen("s", -15, 0.0, 15, 0.1, 3.0, (0.0, 1.0))
    return b


def _k_free(orientation: str | None):
    p = parse_payload(HeavyPayload, heavy_payload(
        _free_screen(orientation).build(phantom=(-15, -15, 15, 15, 6.0)), "volume3d", 270.0, 1.0,
        SCHEDULE))
    case = build_volume_case(p)
    stepper = fastest(case.problem)
    SimulationRunner(case, stepper, lambda *_: False).run()
    shape = case.problem.shape
    f = plan_output(case, to_host(stepper.avg_u).reshape((-1,) + shape),
                    to_host(stepper.avg_u2).reshape(shape))
    stepper.close()
    g = p.grid.output
    return (f.arrays["K"], g.origin_x + (np.arange(g.nx) + 0.5) * g.dx_m,
            g.origin_y + (np.arange(g.ny) + 0.5) * g.dx_m)


@pytest.fixture(scope="module")
def open_ground():
    return _k_free(None)


def test_perpendicular_celosia_shelters_its_lee(open_ground) -> None:
    screened = _k_free("perpendicular")
    before, after = _mean(open_ground, 1, 15, -10, 10), _mean(screened, 1, 15, -10, 10)
    print(f"lee of a perpendicular celosia K {before:.3f} -> {after:.3f}")
    assert after <= 0.9 * before


def test_parallel_celosia_barely_changes_the_flow(open_ground) -> None:
    screened = _k_free("parallel")
    before, after = _mean(open_ground, -15, 15, 1, 15), _mean(screened, -15, 15, 1, 15)
    print(f"beside a parallel celosia K {before:.3f} -> {after:.3f}")
    assert abs(after - before) <= 0.03 * before
