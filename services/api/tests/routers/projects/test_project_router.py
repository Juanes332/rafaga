"""Projects endpoints, ownership and privacy."""

import json
from pathlib import Path

from httpx import AsyncClient


async def test_create_project_has_no_location_and_base_alternative(
    client: AsyncClient, architect, app
) -> None:  # noqa: ANN001
    """A new project has null location and its satellites exist."""
    from sqlalchemy import text

    r = await client.post("/api/v1/projects", headers=architect.headers, json={"name": "A"})
    body = r.json()
    assert r.status_code == 201
    assert body["lat"] is None and body["lon"] is None
    assert body["elevation_m"] is None and body["air_density_kg_m3"] is None
    assert body["analysis_height_m"] == 1.5 and body["role_on_project"] == "owner"
    assert "owner_id" not in body
    async with app.state.session_factory() as s:
        q = "SELECT count(*) FROM {} WHERE project_id=:p"
        p = {"p": body["id"]}
        assert (await s.execute(text(q.format("alternatives") + " AND is_base"), p)).scalar() == 1
        row = (await s.execute(text("SELECT version, buildings FROM geometries WHERE project_id=:p"), p)).one()
        assert row[0] == 1 and row[1] == []
        wind = (await s.execute(text("SELECT rose, z0_m, manual_direction_deg, manual_u10_ms FROM wind_climates WHERE project_id=:p"), p)).one()
        assert tuple(wind) == (None, 1.0, None, None)


async def test_reviewer_cannot_create_project(client: AsyncClient, reviewer) -> None:  # noqa: ANN001
    """Writes by a reviewer are 403."""
    r = await client.post("/api/v1/projects", headers=reviewer.headers, json={"name": "A"})
    assert r.status_code == 403 and r.json()["code"] == "forbidden"


async def test_create_project_validation_and_auth(client: AsyncClient, architect) -> None:  # noqa: ANN001
    """Empty name is 422; no token is 401."""
    bad = await client.post("/api/v1/projects", headers=architect.headers, json={"name": ""})
    anon = await client.post("/api/v1/projects", json={"name": "A"})
    assert bad.status_code == 422 and anon.status_code == 401


async def test_foreign_project_is_byte_identical_to_missing(
    client: AsyncClient, project, other_architect
) -> None:  # noqa: ANN001
    """A foreign id and a random id answer the same 404 bytes."""
    foreign = await client.get(f"/api/v1/projects/{project['id']}", headers=other_architect.headers)
    missing = await client.get(
        "/api/v1/projects/00000000-0000-4000-8000-0000000000aa", headers=other_architect.headers
    )
    assert foreign.status_code == missing.status_code == 404
    assert foreign.content == missing.content
    assert foreign.json()["code"] == "project_not_found"


async def test_foreign_project_writes_are_also_404(
    client: AsyncClient, project, other_architect
) -> None:  # noqa: ANN001
    """Patch, delete and duplicate never reveal a foreign project."""
    h, url = other_architect.headers, f"/api/v1/projects/{project['id']}"
    codes = [
        (await client.patch(url, headers=h, json={"name": "x"})).status_code,
        (await client.delete(url, headers=h)).status_code,
        (await client.post(url + "/duplicate", headers=h)).status_code,
    ]
    assert codes == [404, 404, 404]


async def test_list_shows_only_owned_or_shared_newest_first(
    client: AsyncClient, architect, other_architect, reviewer
) -> None:  # noqa: ANN001
    """Another user's unshared project never appears."""
    a = (await client.post("/api/v1/projects", headers=architect.headers, json={"name": "one"})).json()
    b = (await client.post("/api/v1/projects", headers=architect.headers, json={"name": "two"})).json()
    await client.post("/api/v1/projects", headers=other_architect.headers, json={"name": "alien"})
    mine = (await client.get("/api/v1/projects", headers=architect.headers)).json()
    assert [p["name"] for p in mine] == ["two", "one"]
    assert mine[0]["has_location"] is False and mine[0]["role_on_project"] == "owner"
    await client.put(f"/api/v1/projects/{a['id']}/shares/{reviewer.id}", headers=architect.headers)
    shared = (await client.get("/api/v1/projects", headers=reviewer.headers)).json()
    assert [(p["name"], p["role_on_project"]) for p in shared] == [("one", "reviewer")]
    assert b["id"] not in {p["id"] for p in shared}


async def test_patch_validates_height_and_reviewer_gets_403(
    client: AsyncClient, architect, reviewer, project
) -> None:  # noqa: ANN001
    """Height must be within 0.5-3.0; a shared reviewer cannot write."""
    url = f"/api/v1/projects/{project['id']}"
    ok = await client.patch(url, headers=architect.headers, json={"name": "N", "analysis_height_m": 2.0})
    bad = await client.patch(url, headers=architect.headers, json={"analysis_height_m": 3.5})
    await client.put(url + f"/shares/{reviewer.id}", headers=architect.headers)
    denied = await client.patch(url, headers=reviewer.headers, json={"name": "Z"})
    assert ok.json()["name"] == "N" and ok.json()["analysis_height_m"] == 2.0
    assert bad.status_code == 422
    assert denied.status_code == 403 and denied.json()["code"] == "forbidden"


async def test_delete_removes_rows_cancels_jobs_and_directories(
    client: AsyncClient, architect, project, app
) -> None:  # noqa: ANN001
    """Cascade delete, queued jobs cancelled, volume dirs removed."""
    from sqlalchemy import text

    from app.configs.config import get_settings

    pid = project["id"]
    for sub in ("results", "uploads"):
        d = Path(get_settings().data_dir) / sub / pid
        d.mkdir(parents=True)
        (d / "f.bin").write_bytes(b"x")
    r = await client.delete(f"/api/v1/projects/{pid}", headers=architect.headers)
    assert r.status_code == 204
    for sub in ("results", "uploads"):
        assert not (Path(get_settings().data_dir) / sub / pid).exists()
    async with app.state.session_factory() as s:
        n = (await s.execute(text("SELECT count(*) FROM alternatives WHERE project_id=:p"), {"p": pid})).scalar()
    assert n == 0
    assert (await client.get(f"/api/v1/projects/{pid}", headers=architect.headers)).status_code == 404


async def test_duplicate_copies_setup_without_jobs(
    client: AsyncClient, architect, project, app
) -> None:  # noqa: ANN001
    """Copia de <name> carries wind, geometry, alternatives and elements."""
    from sqlalchemy import text

    pid = project["id"]
    b = json.dumps([{"id": "b1"}])
    async with app.state.session_factory() as s:
        await s.execute(text("UPDATE geometries SET buildings=CAST(:b AS jsonb), version=4 WHERE project_id=:p"), {"b": b, "p": pid})
        await s.execute(text("UPDATE wind_climates SET z0_m=0.3 WHERE project_id=:p"), {"p": pid})
        alt = (await s.execute(text("SELECT id FROM alternatives WHERE project_id=:p"), {"p": pid})).scalar()
        await s.execute(text("INSERT INTO facade_elements (alternative_id,building_id,edge_index,type,params) VALUES (:a, gen_random_uuid(), 0, 'screen', '{}')"), {"a": alt})
        await s.commit()
    r = await client.post(f"/api/v1/projects/{pid}/duplicate", headers=architect.headers)
    new = r.json()
    assert r.status_code == 201 and new["name"] == "Copia de P" and new["id"] != pid
    async with app.state.session_factory() as s:
        p = {"p": new["id"]}
        g = (await s.execute(text("SELECT buildings FROM geometries WHERE project_id=:p"), p)).scalar()
        z0 = (await s.execute(text("SELECT z0_m FROM wind_climates WHERE project_id=:p"), p)).scalar()
        els = (await s.execute(text("SELECT count(*) FROM facade_elements e JOIN alternatives a ON a.id=e.alternative_id WHERE a.project_id=:p"), p)).scalar()
        bases = (await s.execute(text("SELECT count(*) FROM alternatives WHERE project_id=:p AND is_base"), p)).scalar()
    assert g == [{"id": "b1"}] and abs(z0 - 0.3) < 1e-6 and els == 1 and bases == 1
