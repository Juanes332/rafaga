"""2D plan blockage rule: the solver widens the lattice laterally to <= 5 %."""

import numpy as np
import pytest

from app.models.jobs.payload_parser import parse_payload
from app.models.jobs.payload_schemas import HeavyPayload
from app.services.lbm2d.lbm2d_case import build_plan_case
from app.services.simulation.domain_rules import (
    PLAN_BLOCKAGE_LIMIT,
    plan_blockage,
    widened_payload,
)
from tests.support.scenario_factory import SceneBuilder, heavy_payload


def _three_blocks() -> dict:
    b = SceneBuilder()
    b.block("A", 0, 0, 40, 12, 18).block("B", 0, 22, 40, 34, 18).block("C", 46, 4, 58, 29, 15)
    return b.build()


@pytest.mark.parametrize("phi", [292.5, 22.5, 270.0])
def test_contract_grid_is_too_narrow_and_widening_meets_the_limit(phi) -> None:
    p = parse_payload(HeavyPayload, heavy_payload(_three_blocks(), "plan2d", phi, 1.0))
    assert plan_blockage(p) > PLAN_BLOCKAGE_LIMIT
    wide = widened_payload(p)
    assert plan_blockage(wide) <= PLAN_BLOCKAGE_LIMIT
    centre = lambda g: g.origin[1] + g.ny * g.dx_m / 2  # noqa: E731
    assert centre(wide.grid.sim) == pytest.approx(centre(p.grid.sim), abs=p.grid.sim.dx_m)
    assert wide.grid.output == p.grid.output


def test_plan_case_uses_the_widened_lattice() -> None:
    p = parse_payload(HeavyPayload, heavy_payload(_three_blocks(), "plan2d", 292.5, 2.0))
    case = build_plan_case(p)
    assert case.problem.shape[0] == widened_payload(p).grid.sim.ny > p.grid.sim.ny
    assert plan_blockage(case.payload) <= PLAN_BLOCKAGE_LIMIT
    assert np.isin(case.problem.mask, (0, 1, 2)).all()


def test_volume_payload_is_left_alone() -> None:
    p = parse_payload(HeavyPayload, heavy_payload(_three_blocks(), "volume3d", 292.5, 4.0))
    assert widened_payload(p) is p


def test_low_reynolds_only_below_the_sharp_edge_limit() -> None:
    from app.services.lattice.lattice_units import lattice_units
    from app.services.simulation.simulation_case import reynolds_warnings

    def warn(dx: float) -> list[dict]:
        p = parse_payload(HeavyPayload, heavy_payload(_three_blocks(), "plan2d", 292.5, dx))
        return reynolds_warnings(p, lattice_units(0.05, dx, 3.8, 5e-5))

    fine, coarse = warn(1.0), warn(3.0)
    assert "low_reynolds" not in {w["code"] for w in fine}  # H = 18 cells, Re_H = 1.8e4
    assert "low_reynolds" in {w["code"] for w in coarse}  # H = 6 cells


def test_plan_case_caps_a_wall_distance_mixing_length() -> None:
    from app.services.boundary.abl_closure import KAPPA

    p = parse_payload(HeavyPayload, heavy_payload(_three_blocks(), "plan2d", 292.5, 1.0))
    lm = build_plan_case(p).problem.mixing_length
    assert lm is not None
    assert lm.max() == pytest.approx(KAPPA * 0.1 * 18.0, rel=1e-5)
    assert lm.min() >= 0.17


def _volume(top_h: float, dx: float = 4.0):
    p = parse_payload(HeavyPayload, heavy_payload(_three_blocks(), "volume3d", 292.5, dx))
    sim = p.grid.sim.model_copy(update={"nz": int(np.ceil(top_h * 18.0 / dx))})
    return p.model_copy(update={"grid": p.grid.model_copy(update={"sim": sim})})


def test_low_volume_top_is_raised_to_five_building_heights() -> None:
    from app.services.simulation.domain_rules import MIN_TOP_H, raised_top_payload

    p = _volume(2.5)
    raised, warnings = raised_top_payload(p, max_nodes=None)
    assert raised.grid.sim.nz * raised.grid.sim.dx_m >= MIN_TOP_H * 18.0
    assert raised.grid.sim.nz * raised.grid.sim.dx_m < MIN_TOP_H * 18.0 + 4.0
    assert raised.grid.output == p.grid.output and warnings == []


def test_volume_top_above_five_heights_and_plan_payloads_are_untouched() -> None:
    from app.services.simulation.domain_rules import raised_top_payload

    p = _volume(6.0)
    assert raised_top_payload(p, max_nodes=None) == (p, [])
    plan = parse_payload(HeavyPayload, heavy_payload(_three_blocks(), "plan2d", 292.5, 2.0))
    assert raised_top_payload(plan, max_nodes=None) == (plan, [])


def test_raise_that_does_not_fit_is_capped_with_a_warning() -> None:
    from app.services.simulation.domain_rules import raised_top_payload

    p = _volume(2.5)
    sim = p.grid.sim
    layer = sim.nx * sim.ny
    capped, warnings = raised_top_payload(p, max_nodes=layer * (sim.nz + 3))
    assert capped.grid.sim.nz == sim.nz + 3
    assert warnings == [{"code": "domain_top_capped", "ref": p.scene.source_ref()}]
