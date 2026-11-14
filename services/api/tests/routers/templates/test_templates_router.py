"""Templates endpoints."""

from httpx import AsyncClient

GOOD = {"name": "T", "payload": {"terrain_category": "suburban", "z0_m": 0.3,
        "thresholds": {"k_accel": 1.4, "k_stagnation": 0.35, "dk_reduction": -0.15}}}


async def test_create_list_and_delete_template(client: AsyncClient, architect) -> None:  # noqa: ANN001
    """The round trip returns 201, the list, then 204."""
    c = await client.post("/api/v1/templates", headers=architect.headers, json=GOOD)
    listed = await client.get("/api/v1/templates", headers=architect.headers)
    d = await client.delete(f"/api/v1/templates/{c.json()['id']}", headers=architect.headers)
    assert c.status_code == 201 and c.json()["name"] == "T"
    assert [t["name"] for t in listed.json()] == ["T"] and d.status_code == 204


async def test_location_keys_are_rejected_at_any_depth(client: AsyncClient, architect) -> None:  # noqa: ANN001
    """lat/lon/elevation/location keys never get stored."""
    for payload in (
        {"lat": 1.0}, {"facade_defaults": {"deep": [{"Longitude": 2}]}},
        {"elevation": 5}, {"location": {}}, {"latitude": 1}, {"lon": 1}, {"longitude": 1},
    ):
        r = await client.post("/api/v1/templates", headers=architect.headers,
                              json={"name": "x", "payload": payload})
        assert (r.status_code, r.json()["code"]) == (422, "template_contains_location")


async def test_unknown_keys_and_bad_ranges_are_validation_errors(client: AsyncClient, architect) -> None:  # noqa: ANN001
    """Keys outside the schema or z0 out of range answer 422."""
    for payload in ({"surprise": 1}, {"z0_m": 9}):
        r = await client.post("/api/v1/templates", headers=architect.headers,
                              json={"name": "x", "payload": payload})
        assert (r.status_code, r.json()["code"]) == (422, "validation_error")
    assert (await client.post("/api/v1/templates", headers=architect.headers,
                              json={"payload": {}})).status_code == 422


async def test_foreign_template_delete_equals_missing(
    client: AsyncClient, architect, other_architect
) -> None:  # noqa: ANN001
    """A foreign id answers the same 404 bytes as a random one."""
    c = await client.post("/api/v1/templates", headers=architect.headers, json=GOOD)
    foreign = await client.delete(f"/api/v1/templates/{c.json()['id']}", headers=other_architect.headers)
    missing = await client.delete(
        "/api/v1/templates/00000000-0000-4000-8000-0000000000aa", headers=other_architect.headers)
    assert foreign.status_code == missing.status_code == 404
    assert foreign.content == missing.content and foreign.json()["code"] == "template_not_found"
    assert (await client.get("/api/v1/templates", headers=other_architect.headers)).json() == []


async def test_apply_template_sets_roughness_and_thresholds_not_location(
    client: AsyncClient, architect, project
) -> None:  # noqa: ANN001
    """The wind roughness and the caller's thresholds change; location stays null."""
    tid = (await client.post("/api/v1/templates", headers=architect.headers, json=GOOD)).json()["id"]
    r = await client.post(f"/api/v1/projects/{project['id']}/apply-template",
                          headers=architect.headers, json={"template_id": tid})
    s = await client.get("/api/v1/settings", headers=architect.headers)
    p = await client.get(f"/api/v1/projects/{project['id']}", headers=architect.headers)
    assert r.status_code == 200
    assert (r.json()["terrain_category"], round(r.json()["z0_m"], 3)) == ("suburban", 0.3)
    assert s.json()["thresholds"]["k_accel"] == 1.4
    assert p.json()["lat"] is None and p.json()["lon"] is None


async def test_apply_template_errors(
    client: AsyncClient, architect, other_architect, reviewer, project
) -> None:  # noqa: ANN001
    """Unknown template 404, foreign project 404, reviewer 403, anonymous 401."""
    url = f"/api/v1/projects/{project['id']}/apply-template"
    tid = (await client.post("/api/v1/templates", headers=architect.headers, json=GOOD)).json()["id"]
    unknown = await client.post(url, headers=architect.headers,
                                json={"template_id": "00000000-0000-4000-8000-0000000000aa"})
    foreign = await client.post(url, headers=other_architect.headers, json={"template_id": tid})
    await client.put(f"/api/v1/projects/{project['id']}/shares/{reviewer.id}", headers=architect.headers)
    denied = await client.post(url, headers=reviewer.headers, json={"template_id": tid})
    anon = await client.post(url, json={"template_id": tid})
    assert unknown.json()["code"] == "template_not_found" and unknown.status_code == 404
    assert foreign.json()["code"] == "project_not_found" and foreign.status_code == 404
    assert denied.status_code == 403 and anon.status_code == 401
