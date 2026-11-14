"""Pure scene compilation: setbacks, degenerate elements, clamps."""

from uuid import uuid4

from app.services.scene.scene_compiler import compile_scene
from tests.support.scene_support import BUILDING_ID, assert_valid_scene, square_building


def _compile(elements, buildings=None):  # noqa: ANN001, ANN202
    return compile_scene(
        project_id=str(uuid4()), alternative_id=str(uuid4()), geometry_version=1,
        buildings=buildings or [square_building()], elements=elements,
        z0_m=0.3, analysis_height_m=1.5, vegetation_cd=0.2, envelope_m=10,
    )


def _el(type_, edge=0, **params):  # noqa: ANN001, ANN202
    return {"id": str(uuid4()), "building_id": BUILDING_ID, "edge_index": edge, "type": type_, "params": params}


def test_setback_stacks_offset_tiers() -> None:
    """Each tier above start_floor moves the edge in by another setback."""
    el = _el("setback", edge=0, setback_m=1.0, floor_height_m=3.0, start_floor=1)
    scene = _compile([el])
    tiers = [s for s in scene["solids"] if s["origin"]["kind"] == "setback_tier"]
    assert_valid_scene(scene)
    assert tiers[0]["z_min"] == 0 and tiers[1]["z_min"] == 3.0 and tiers[-1]["z_max"] == 24.0
    ys = [min(p[1] for p in t["footprint"]) for t in tiers]
    assert ys[:3] == [-15.0, -14.0, -13.0]


def test_setback_degenerate_tier_truncates_with_warning() -> None:
    """A tier that would vanish stops the stack and is reported."""
    el = _el("setback", edge=0, setback_m=5.0, floor_height_m=2.5, start_floor=1)
    scene = _compile([el])
    assert {"code": "setback_tiers_truncated", "ref": el["id"]} in scene["warnings"]
    assert max(s["z_max"] for s in scene["solids"]) == 24.0
    assert_valid_scene(scene)


def test_screen_taller_than_building_is_clamped() -> None:
    """A 50 m screen on a 5 m building is cut with a warning."""
    el = _el("screen", height_m=50)
    scene = _compile([el], [square_building(height=5)])
    assert scene["porous"][0]["z_max"] == 5.0
    assert {"code": "above_building_clamped", "ref": el["id"]} in scene["warnings"]


def test_low_screen_below_analysis_height_is_flagged() -> None:
    """A 1 m screen never reaches the 1.5 m analysis plane."""
    el = _el("screen", height_m=1.0)
    assert {"code": "below_analysis_height", "ref": el["id"]} in _compile([el])["warnings"]


def test_fins_count_follows_the_generation_rule() -> None:
    """floor((L - t) / pitch) + 1 fins, each thin_axis = thickness."""
    el = _el("fins", edge=1, pitch_m=3.0, thickness_m=0.2, depth_m=0.5)
    fins = [s for s in _compile([el])["solids"] if s["origin"]["kind"] == "fin"]
    assert len(fins) == int((30 - 0.2) // 3.0) + 1 and fins[0]["thin_axis_m"] == 0.2


def test_canopy_sits_between_height_and_height_plus_thickness() -> None:
    """The canopy slab is 0.3 m thick starting at height_m."""
    c = next(s for s in _compile([_el("canopy", height_m=3.5)])["solids"] if s["origin"]["kind"] == "canopy")
    assert (c["z_min"], c["z_max"], c["thin_axis_m"]) == (3.5, 3.8, 0.3)


def test_tiers_replace_the_single_building_solid() -> None:
    """Imported tiers become building_tier solids."""
    b = square_building()
    b["tiers"] = [
        {"z_from": 0, "z_to": 3, "footprint": b["footprint"]},
        {"z_from": 3, "z_to": 24, "footprint": [[-5, -5], [5, -5], [5, 5], [-5, 5]]},
    ]
    solids = _compile([], [b])["solids"]
    assert [s["origin"]["kind"] for s in solids] == ["building_tier"] * 2


def test_h_max_and_bounds_use_all_base_buildings() -> None:
    """Bounds span every building; h_max is the tallest."""
    second = square_building(height=40, building_id="22222222-2222-4222-8222-222222222222")
    second["footprint"] = [[20, 0], [30, 0], [30, 10], [20, 10]]
    scene = _compile([], [square_building(), second])
    assert scene["h_max_m"] == 40 and scene["bounds"]["base_max"] == [30, 15, 40]
    assert_valid_scene(scene)
