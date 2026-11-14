"""Alternatives endpoints (API-36..39, ENT-09)."""

import json

from httpx import AsyncClient
from sqlalchemy import text

from tests.support.scene_support import add_alternative, base_alternative_id, insert_result

MISSING = "00000000-0000-4000-8000-0000000000cc"


async def test_list_has_base_first_with_counts(client: AsyncClient, architect, project) -> None:  # noqa: ANN001
    """Base comes first, undeletable, with zero elements and no summary."""
    url = f"/api/v1/projects/{project['id']}/alternatives"
    await add_alternative(client, architect.headers, project["id"], "B")
    r = await client.get(url, headers=architect.headers)
    assert r.status_code == 200
    first, second = r.json()
    assert first["is_base"] and first["name"] == "Caso base" and first["element_count"] == 0
    assert first["latest_results_summary"] is None and second["position"] > first["position"]


async def test_list_requires_auth_and_hides_foreign(client: AsyncClient, project, other_architect) -> None:  # noqa: ANN001
    """401 without token; foreign equals missing byte for byte."""
    url = f"/api/v1/projects/{project['id']}/alternatives"
    assert (await client.get(url)).status_code == 401
    foreign = await client.get(url, headers=other_architect.headers)
    missing = await client.get(f"/api/v1/projects/{MISSING}/alternatives", headers=other_architect.headers)
    assert foreign.status_code == 404 and foreign.content == missing.content


async def test_latest_results_summary(client: AsyncClient, architect, project, app) -> None:  # noqa: ANN001
    """The summary reports the latest study with the mean K."""
    base = await base_alternative_id(client, architect.headers, project["id"])
    await insert_result(app, project["id"], base, architect.id, 0.8)
    alts = (await client.get(f"/api/v1/projects/{project['id']}/alternatives", headers=architect.headers)).json()
    s = alts[0]["latest_results_summary"]
    assert s["kind"] == "plan2d" and s["status"] == "completed" and abs(s["k_mean"] - 0.8) < 1e-6


async def test_create_copies_base_elements_by_default(client: AsyncClient, architect, built) -> None:  # noqa: ANN001
    """A new alternative inherits the facade elements of the base."""
    await client.post(f"/api/v1/alternatives/{built['alt_id']}/facade-elements?confirm_base_change=true",
                      headers=architect.headers,
                      json={"building_id": built["building_id"], "edge_index": 0, "type": "screen"})
    alt = await add_alternative(client, architect.headers, built["project_id"])
    els = await client.get(f"/api/v1/alternatives/{alt['id']}/facade-elements", headers=architect.headers)
    assert alt["is_base"] is False and len(els.json()) == 1


async def test_create_from_other_alternative(client: AsyncClient, architect, built) -> None:  # noqa: ANN001
    """from_alternative_id selects the source of the copy."""
    a = await add_alternative(client, architect.headers, built["project_id"], "A")
    await client.post(f"/api/v1/alternatives/{a['id']}/facade-elements", headers=architect.headers,
                      json={"building_id": built["building_id"], "edge_index": 1, "type": "canopy"})
    r = await client.post(f"/api/v1/projects/{built['project_id']}/alternatives", headers=architect.headers,
                          json={"name": "C", "from_alternative_id": a["id"]})
    els = (await client.get(f"/api/v1/alternatives/{r.json()['id']}/facade-elements", headers=architect.headers)).json()
    assert r.status_code == 201 and [e["type"] for e in els] == ["canopy"]


async def test_create_validation_and_reviewer_forbidden(client: AsyncClient, architect, reviewer, project) -> None:  # noqa: ANN001
    """Empty names are 422; a shared reviewer is 403."""
    url = f"/api/v1/projects/{project['id']}/alternatives"
    assert (await client.post(url, headers=architect.headers, json={"name": ""})).status_code == 422
    await client.put(f"/api/v1/projects/{project['id']}/shares/{reviewer.id}", headers=architect.headers)
    r = await client.post(url, headers=reviewer.headers, json={"name": "x"})
    assert r.status_code == 403 and r.json()["code"] == "forbidden"


async def test_ninth_alternative_hits_the_default_limit(client: AsyncClient, architect, project) -> None:  # noqa: ANN001
    """Eight derived alternatives fit; the ninth is 409 with the limit."""
    for i in range(8):
        await add_alternative(client, architect.headers, project["id"], f"A{i}")
    r = await client.post(f"/api/v1/projects/{project['id']}/alternatives", headers=architect.headers, json={"name": "N"})
    assert r.status_code == 409 and r.json()["code"] == "alternatives_limit"
    assert r.json()["details"] == {"limit": 8}


async def test_user_setting_overrides_the_limit(client: AsyncClient, architect, project, app) -> None:  # noqa: ANN001
    """user_settings.alternatives_limit wins over the default."""
    async with app.state.session_factory() as s:
        await s.execute(text("INSERT INTO user_settings VALUES (:u, '{}', '{}', 0.25, 0.2, 1)"), {"u": architect.id})
        await s.commit()
    await add_alternative(client, architect.headers, project["id"], "A")
    r = await client.post(f"/api/v1/projects/{project['id']}/alternatives", headers=architect.headers, json={"name": "B"})
    assert r.status_code == 409 and r.json()["details"] == {"limit": 1}


async def test_patch_renames_and_reorders(client: AsyncClient, architect, project) -> None:  # noqa: ANN001
    """Rename is returned by the list; position moves the alternative."""
    a = await add_alternative(client, architect.headers, project["id"], "A")
    b = await add_alternative(client, architect.headers, project["id"], "B")
    r = await client.patch(f"/api/v1/alternatives/{b['id']}", headers=architect.headers, json={"name": "Bee", "position": 1})
    names = [x["name"] for x in (await client.get(f"/api/v1/projects/{project['id']}/alternatives", headers=architect.headers)).json()]
    assert r.status_code == 200 and r.json()["name"] == "Bee"
    assert names == ["Caso base", "Bee", "A"] and a["id"]


async def test_patch_validation_and_privacy(client: AsyncClient, architect, other_architect, project) -> None:  # noqa: ANN001
    """81-char names are 422; foreign equals missing."""
    a = await add_alternative(client, architect.headers, project["id"])
    url = f"/api/v1/alternatives/{a['id']}"
    assert (await client.patch(url, headers=architect.headers, json={"name": "x" * 81})).status_code == 422
    foreign = await client.patch(url, headers=other_architect.headers, json={"name": "z"})
    missing = await client.patch(f"/api/v1/alternatives/{MISSING}", headers=other_architect.headers, json={"name": "z"})
    assert foreign.status_code == 404 and foreign.content == missing.content
    assert foreign.json()["code"] == "alternative_not_found"
    assert (await client.patch(url, json={"name": "z"})).status_code == 401


async def test_delete_removes_elements_and_base_is_undeletable(client: AsyncClient, architect, built, app) -> None:  # noqa: ANN001
    """Non-base delete cascades elements; the base answers 409."""
    a = await add_alternative(client, architect.headers, built["project_id"])
    await client.post(f"/api/v1/alternatives/{a['id']}/facade-elements", headers=architect.headers,
                      json={"building_id": built["building_id"], "edge_index": 0, "type": "screen"})
    gone = await client.delete(f"/api/v1/alternatives/{a['id']}", headers=architect.headers)
    base = await client.delete(f"/api/v1/alternatives/{built['alt_id']}", headers=architect.headers)
    async with app.state.session_factory() as s:
        n = (await s.execute(text("SELECT count(*) FROM facade_elements WHERE alternative_id=:a"), {"a": a["id"]})).scalar()
    assert gone.status_code == 204 and n == 0
    assert base.status_code == 409 and base.json()["code"] == "base_undeletable"


async def test_delete_reviewer_forbidden(client: AsyncClient, architect, reviewer, project) -> None:  # noqa: ANN001
    """A shared reviewer cannot delete."""
    a = await add_alternative(client, architect.headers, project["id"])
    await client.put(f"/api/v1/projects/{project['id']}/shares/{reviewer.id}", headers=architect.headers)
    assert (await client.delete(f"/api/v1/alternatives/{a['id']}", headers=reviewer.headers)).status_code == 403
    assert json.dumps(a)
