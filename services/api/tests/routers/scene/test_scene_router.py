"""GET /alternatives/{id}/scene (API-45)."""

import json

from httpx import AsyncClient
from sqlalchemy import text

from tests.support.scene_support import (
    CONTRACTS,
    BUILDING_ID,
    assert_valid_scene,
    set_geometry,
    square_building,
)

MISSING = "00000000-0000-4000-8000-0000000000ee"


async def _add(client, architect, built, type_, edge=0, params=None):  # noqa: ANN001, ANN202
    r = await client.post(
        f"/api/v1/alternatives/{built['alt_id']}/facade-elements?confirm_base_change=true",
        headers=architect.headers,
        json={"building_id": BUILDING_ID, "edge_index": edge, "type": type_, "params": params or {}},
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _scene(client, architect, built):  # noqa: ANN001, ANN202
    r = await client.get(f"/api/v1/alternatives/{built['alt_id']}/scene", headers=architect.headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_contract_example_is_valid_against_the_schema() -> None:
    """The validator accepts the normative example."""
    assert_valid_scene(json.loads((CONTRACTS / "examples/scene.example.json").read_text()))


async def test_plain_building_scene_is_schema_valid(client: AsyncClient, architect, built) -> None:  # noqa: ANN001
    """A building alone compiles to one solid and valid metadata."""
    scene = await _scene(client, architect, built)
    assert_valid_scene(scene)
    assert scene["h_max_m"] == 24.0 and scene["ground"]["z0_m"] == 1.0
    assert scene["analysis_height_m"] == 1.5 and scene["source"]["geometry_version"] == 3
    assert scene["bounds"] == {"base_min": [-10, -15, 0], "base_max": [10, 15, 24], "envelope_m": 10}
    assert [s["id"] for s in scene["solids"]] == [f"b:{BUILDING_ID}:t0"] and scene["porous"] == []
    assert "lat" not in json.dumps(scene)


async def test_all_strategies_compile_and_validate(client: AsyncClient, architect, built) -> None:  # noqa: ANN001
    """Every strategy yields valid primitives of the right kind."""
    for i, t in enumerate(["screen", "fins", "canopy", "vegetation", "setback"]):
        await _add(client, architect, built, t, edge=i % 4)
    scene = await _scene(client, architect, built)
    assert_valid_scene(scene)
    kinds = {s["origin"]["kind"] for s in scene["solids"]}
    assert {"fin", "canopy", "setback_tier"} <= kinds
    assert {p["model"] for p in scene["porous"]} == {"screen", "vegetation"}


async def test_screen_loss_coefficient_follows_idelchik(client: AsyncClient, architect, built) -> None:  # noqa: ANN001
    """beta 0.4 gives zeta of about 8.23 and an outward normal."""
    await _add(client, architect, built, "screen", edge=0, params={"porosity": 0.4})
    p = (await _scene(client, architect, built))["porous"][0]
    assert abs(p["loss_coefficient"] - 8.2317) < 1e-3 and p["normal"] == [0.0, -1.0]
    assert p["thickness_m"] == 0.1 and p["z_max"] == 3.0
    assert sorted(p["footprint"]) == sorted([[-10, -15.6], [10, -15.6], [10, -15.5], [-10, -15.5]])


async def test_vegetation_uses_the_owner_vegetation_cd(client: AsyncClient, architect, built, app) -> None:  # noqa: ANN001
    """drag_coefficient comes from user_settings, 0.2 without a row."""
    await _add(client, architect, built, "vegetation")
    assert (await _scene(client, architect, built))["porous"][0]["drag_coefficient"] == 0.2
    async with app.state.session_factory() as s:
        await s.execute(text("INSERT INTO user_settings VALUES (:u,'{}','{}',0.25,0.35,8)"), {"u": architect.id})
        await s.commit()
    assert (await _scene(client, architect, built))["porous"][0]["drag_coefficient"] == 0.35


async def test_orphaned_element_is_skipped_with_warning(client: AsyncClient, architect, built, app) -> None:  # noqa: ANN001
    """A vanished edge is skipped and reported."""
    el = await _add(client, architect, built, "screen", edge=3)
    tri = square_building()
    tri["footprint"] = [[0, 0], [5, 0], [0, 5]]
    await set_geometry(app, built["project_id"], [tri])
    scene = await _scene(client, architect, built)
    assert scene["porous"] == [] and scene["warnings"] == [{"code": "element_orphaned", "ref": el["id"]}]
    assert_valid_scene(scene)


async def test_deleting_an_element_removes_its_primitives(client: AsyncClient, architect, built) -> None:  # noqa: ANN001
    """The next scene has no primitive of the deleted element."""
    el = await _add(client, architect, built, "fins")
    before = await _scene(client, architect, built)
    await client.delete(f"/api/v1/facade-elements/{el['id']}?confirm_base_change=true", headers=architect.headers)
    after = await _scene(client, architect, built)
    refs = lambda sc: {p["origin"]["element_id"] for p in sc["solids"] + sc["porous"]}  # noqa: E731
    assert el["id"] in refs(before) and el["id"] not in refs(after)


async def test_scene_privacy_auth_and_no_buildings(client: AsyncClient, architect, other_architect, built, project) -> None:  # noqa: ANN001
    """Foreign equals missing; 401; empty geometry is 409 no_buildings."""
    url = f"/api/v1/alternatives/{built['alt_id']}/scene"
    f = await client.get(url, headers=other_architect.headers)
    m = await client.get(f"/api/v1/alternatives/{MISSING}/scene", headers=other_architect.headers)
    assert f.status_code == 404 and f.content == m.content
    assert (await client.get(url)).status_code == 401
    p2 = (await client.post("/api/v1/projects", headers=architect.headers, json={"name": "E"})).json()
    alt = (await client.get(f"/api/v1/projects/{p2['id']}/alternatives", headers=architect.headers)).json()[0]["id"]
    r = await client.get(f"/api/v1/alternatives/{alt}/scene", headers=architect.headers)
    assert r.status_code == 409 and r.json()["code"] == "no_buildings" and project
