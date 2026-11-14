"""Facade strategies and elements (API-40..44, ENT-10)."""

from httpx import AsyncClient

from tests.support.scene_support import add_alternative, set_geometry, square_building

MISSING = "00000000-0000-4000-8000-0000000000dd"


def _body(built, **kw):  # noqa: ANN001, ANN202
    return {"building_id": built["building_id"], "edge_index": 0, "type": "screen", **kw}


async def test_strategies_catalogue(client: AsyncClient, architect) -> None:  # noqa: ANN001
    """Five strategies with ranges and defaults from one source."""
    r = await client.get("/api/v1/facade-strategies", headers=architect.headers)
    by = {s["type"]: {p["key"]: p for p in s["parameters"]} for s in r.json()}
    assert r.status_code == 200 and set(by) == {"screen", "fins", "canopy", "setback", "vegetation"}
    assert by["screen"]["porosity"]["min"] == 0.05 and by["screen"]["porosity"]["default"] == 0.4
    assert by["fins"]["height_m"]["default"] is None
    assert by["setback"]["start_floor"]["max"] == 100
    assert all({"key", "unit", "min", "max", "default", "help_key"} <= set(p) for s in by.values() for p in s.values())
    assert (await client.get("/api/v1/facade-strategies")).status_code == 401


async def test_create_applies_defaults(client: AsyncClient, architect, built) -> None:  # noqa: ANN001
    """Missing params take catalogue defaults; no adjustments."""
    r = await client.post(f"/api/v1/alternatives/{built['alt_id']}/facade-elements?confirm_base_change=true",
                          headers=architect.headers, json=_body(built))
    assert r.status_code == 201
    assert r.json()["params"] == {"porosity": 0.4, "height_m": 3.0, "offset_m": 0.5}
    assert r.json()["adjustments"] == [] and r.json()["orphaned"] is False


async def test_create_clamps_and_reports(client: AsyncClient, architect, built) -> None:  # noqa: ANN001
    """Out-of-range values are clamped and listed."""
    r = await client.post(f"/api/v1/alternatives/{built['alt_id']}/facade-elements", headers=architect.headers,
                          json=_body(built, params={"porosity": 2.0}))
    assert r.json()["params"]["porosity"] == 0.95
    adj = r.json()["adjustments"][0]
    assert (adj["field"], adj["requested"], adj["applied"]) == ("porosity", 2.0, 0.95)


async def test_create_rejects_unknown_param_and_type(client: AsyncClient, architect, built) -> None:  # noqa: ANN001
    """Unknown params and unknown types are 422 validation_error."""
    url = f"/api/v1/alternatives/{built['alt_id']}/facade-elements"
    a = await client.post(url, headers=architect.headers, json=_body(built, params={"bogus": 1}))
    b = await client.post(url, headers=architect.headers, json=_body(built, type="wall"))
    assert a.status_code == b.status_code == 422 and a.json()["code"] == "validation_error"


async def test_create_edge_not_found(client: AsyncClient, architect, built) -> None:  # noqa: ANN001
    """Unknown edge or building is 422 edge_not_found."""
    url = f"/api/v1/alternatives/{built['alt_id']}/facade-elements"
    a = await client.post(url, headers=architect.headers, json=_body(built, edge_index=9))
    b = await client.post(url, headers=architect.headers, json=_body(built, building_id=MISSING))
    assert a.status_code == b.status_code == 422 and a.json()["code"] == "edge_not_found"


async def test_create_without_buildings_is_409(client: AsyncClient, architect, project) -> None:  # noqa: ANN001
    """A project without buildings answers no_buildings."""
    alt = (await client.get(f"/api/v1/projects/{project['id']}/alternatives", headers=architect.headers)).json()[0]["id"]
    r = await client.post(f"/api/v1/alternatives/{alt}/facade-elements", headers=architect.headers,
                          json={"building_id": MISSING, "edge_index": 0, "type": "screen"})
    assert r.status_code == 409 and r.json()["code"] == "no_buildings"


async def test_base_locked_when_alternatives_exist(client: AsyncClient, architect, built) -> None:  # noqa: ANN001
    """Base writes need confirm_base_change once alternatives exist."""
    await add_alternative(client, architect.headers, built["project_id"])
    url = f"/api/v1/alternatives/{built['alt_id']}/facade-elements"
    locked = await client.post(url, headers=architect.headers, json=_body(built))
    ok = await client.post(url + "?confirm_base_change=true", headers=architect.headers, json=_body(built))
    el = ok.json()
    patched = await client.patch(f"/api/v1/facade-elements/{el['id']}", headers=architect.headers, json={"params": {"offset_m": 1}})
    confirmed = await client.patch(f"/api/v1/facade-elements/{el['id']}", headers=architect.headers,
                                   json={"params": {"offset_m": 1}, "confirm_base_change": True})
    deleted = await client.delete(f"/api/v1/facade-elements/{el['id']}", headers=architect.headers)
    assert locked.status_code == 409 and locked.json()["code"] == "base_locked"
    assert ok.status_code == 201 and patched.status_code == 409 and confirmed.status_code == 200
    assert deleted.status_code == 409


async def test_reviewer_cannot_write(client: AsyncClient, architect, reviewer, built) -> None:  # noqa: ANN001
    """A shared reviewer gets 403 on create and delete, but may list."""
    await client.put(f"/api/v1/projects/{built['project_id']}/shares/{reviewer.id}", headers=architect.headers)
    url = f"/api/v1/alternatives/{built['alt_id']}/facade-elements"
    el = (await client.post(url, headers=architect.headers, json=_body(built))).json()
    c = await client.post(url, headers=reviewer.headers, json=_body(built))
    d = await client.delete(f"/api/v1/facade-elements/{el['id']}", headers=reviewer.headers)
    ls = await client.get(url, headers=reviewer.headers)
    assert (c.status_code, d.status_code, ls.status_code) == (403, 403, 200)


async def test_list_flags_orphans(client: AsyncClient, architect, built, app) -> None:  # noqa: ANN001
    """Elements whose building or edge vanished are orphaned."""
    url = f"/api/v1/alternatives/{built['alt_id']}/facade-elements"
    await client.post(url, headers=architect.headers, json=_body(built))
    await client.post(url, headers=architect.headers, json=_body(built, edge_index=3))
    tri = square_building()
    tri["footprint"] = [[0, 0], [5, 0], [0, 5]]
    await set_geometry(app, built["project_id"], [tri])
    flags = [e["orphaned"] for e in (await client.get(url, headers=architect.headers)).json()]
    assert flags == [False, True]


async def test_patch_merges_clamps_and_reports(client: AsyncClient, architect, built) -> None:  # noqa: ANN001
    """PATCH keeps untouched params, clamps new ones, reports them."""
    url = f"/api/v1/alternatives/{built['alt_id']}/facade-elements"
    el = (await client.post(url, headers=architect.headers, json=_body(built, params={"offset_m": 2}))).json()
    r = await client.patch(f"/api/v1/facade-elements/{el['id']}", headers=architect.headers, json={"params": {"height_m": 99}})
    assert r.json()["params"] == {"porosity": 0.4, "height_m": 50.0, "offset_m": 2.0}
    assert [a["field"] for a in r.json()["adjustments"]] == ["height_m"]


async def test_patch_and_delete_privacy(client: AsyncClient, architect, other_architect, built) -> None:  # noqa: ANN001
    """Foreign element ids equal missing ones; 401 without token."""
    el = (await client.post(f"/api/v1/alternatives/{built['alt_id']}/facade-elements", headers=architect.headers, json=_body(built))).json()
    h = other_architect.headers
    f = await client.patch(f"/api/v1/facade-elements/{el['id']}", headers=h, json={"params": {}})
    m = await client.patch(f"/api/v1/facade-elements/{MISSING}", headers=h, json={"params": {}})
    fd = await client.delete(f"/api/v1/facade-elements/{el['id']}", headers=h)
    md = await client.delete(f"/api/v1/facade-elements/{MISSING}", headers=h)
    assert f.status_code == 404 and f.content == m.content and fd.content == md.content
    assert f.json()["code"] == "element_not_found"
    assert (await client.delete(f"/api/v1/facade-elements/{el['id']}")).status_code == 401


async def test_list_foreign_alternative_is_404(client: AsyncClient, other_architect, built) -> None:  # noqa: ANN001
    """Listing a foreign alternative equals listing a missing one."""
    f = await client.get(f"/api/v1/alternatives/{built['alt_id']}/facade-elements", headers=other_architect.headers)
    m = await client.get(f"/api/v1/alternatives/{MISSING}/facade-elements", headers=other_architect.headers)
    assert f.status_code == 404 and f.content == m.content
