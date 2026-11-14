"""2D plans must say which facade elements they cannot represent."""

from app.models.jobs.payload_parser import parse_payload
from app.models.jobs.payload_schemas import HeavyPayload
from app.services.lbm2d.lbm2d_case import build_plan_case
from app.services.lbm3d.lbm3d_case import build_volume_case
from tests.support.scenario_factory import SceneBuilder, heavy_payload

CODE = "element_not_representable_2d"


def _scene() -> dict:
    b = SceneBuilder().block("A", 0, 0, 30, 12, 18)
    b.canopy("canopy-1", 0, -3, 30, 0, 4.0)
    b.screen("screen-1", 0, -2.1, 30, -2.0, 18, (0.0, -1.0))
    b.fin("fins-1", -0.5, 5.9, 0.0, 6.1, 18)
    return b.build()


def test_plan_case_flags_canopies_once_and_keeps_elements_cut_at_z_a() -> None:
    case = build_plan_case(parse_payload(HeavyPayload, heavy_payload(_scene(), "plan2d", 180.0, 2.0)))
    flagged = [w["ref"] for w in case.warnings if w["code"] == CODE]
    assert flagged == ["canopy-1"]


def test_volume_case_never_flags_elements() -> None:
    case = build_volume_case(parse_payload(HeavyPayload, heavy_payload(_scene(), "volume3d", 180.0, 4.0)))
    assert CODE not in {w["code"] for w in case.warnings}
