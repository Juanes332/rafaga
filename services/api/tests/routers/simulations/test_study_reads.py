"""Study reads, derived status, progress and cancellation."""

import json

from httpx import AsyncClient

from tests.routers.simulations.conftest import set_rose, sql

URL = "/api/v1/simulations"


async def _study(client, architect, ready, dirs=(270,)) -> dict:  # noqa: ANN001
    r = await client.post(URL, headers=architect.headers, json={
        "alternative_id": ready["alternative_id"], "kind": "plan2d",
        "directions_deg": list(dirs), "dx_m": 1.0})
    assert r.status_code == 202
    return r.json()


async def test_progress_and_status_follow_the_jobs(client: AsyncClient, architect, ready, solver, app) -> None:  # noqa: ANN001
    """Values change between polls; status derives per contract 2.1."""
    s = await _study(client, architect, ready, (0, 90))
    first, second = [j["id"] for j in s["jobs"]]
    await sql(app, "UPDATE jobs SET status='running', progress=0.4, phase='spinup', "
              "eta_seconds=30, device_used='cpu' WHERE id=:j", j=first)
    a = (await client.get(f"{URL}/{s['id']}", headers=architect.headers)).json()
    await sql(app, "UPDATE jobs SET progress=0.7 WHERE id=:j", j=first)
    b = (await client.get(f"{URL}/{s['id']}", headers=architect.headers)).json()
    assert a["status"] == "running" and a["progress"] == 0.2 and b["progress"] == 0.35
    job = next(j for j in b["jobs"] if j["id"] == first)
    assert (job["phase"], job["eta_seconds"], job["device_used"]) == ("spinup", 30, "cpu")


async def test_partial_status_and_result_id(client: AsyncClient, architect, ready, solver, app) -> None:  # noqa: ANN001
    """One completed and one failed job make the study partial."""
    s = await _study(client, architect, ready, (0, 90))
    ok, bad = [j["id"] for j in s["jobs"]]
    await sql(app, "UPDATE jobs SET status='completed', progress=1 WHERE id=:j", j=ok)
    await sql(app, "UPDATE jobs SET status='failed', error_code='mesh_too_large', "
              "error_message='x', error_details=CAST(:d AS jsonb) WHERE id=:j",
              j=bad, d=json.dumps({"proposed_dx_m": 1.5}))
    await sql(app, "INSERT INTO results (job_id, study_id, project_id, alternative_id, kind, dx_m, "
              "device, output_grid, stats, convergence, comparability, comparability_key, dir, "
              "fields, images) SELECT id, study_id, project_id, "
              "(SELECT alternative_id FROM studies WHERE id=jobs.study_id), 'plan2d', 1, 'cpu', "
              "'{}','{}','{}','{}','k','d','[]','[]' FROM jobs WHERE id=:j", j=ok)
    full = (await client.get(f"{URL}/{s['id']}", headers=architect.headers)).json()
    by = {j["id"]: j for j in full["jobs"]}
    assert full["status"] == "partial"
    assert by[ok]["result_id"] and by[bad]["result_id"] is None
    assert by[bad]["error"]["code"] == "mesh_too_large" and "1.5" in by[bad]["error"]["hint"]


async def test_coverage_is_none_for_manual_and_set_for_era5(client: AsyncClient, architect, ready, solver, app) -> None:  # noqa: ANN001
    """Coverage needs a rose."""
    manual = await _study(client, architect, ready)
    await set_rose(app, ready["project_id"])
    era = await _study(client, architect, ready, (270, 90))
    assert manual["coverage"] is None and abs(era["coverage"] - 0.12 / 0.96) < 1e-9


async def test_list_is_newest_first_with_summary(client: AsyncClient, architect, ready, solver) -> None:  # noqa: ANN001
    """The listing shows alternative name, kind, directions, status."""
    a, b = await _study(client, architect, ready), await _study(client, architect, ready, (0,))
    r = await client.get(f"/api/v1/projects/{ready['project_id']}/simulations", headers=architect.headers)
    rows = r.json()
    assert [x["id"] for x in rows] == [b["id"], a["id"]]
    assert rows[0]["alternative_name"] == "Caso base" and rows[0]["status"] == "queued"
    assert set(rows[0]) == {"id", "alternative_name", "kind", "directions_deg", "status",
                            "progress", "device", "created_at"}


async def test_cancel_cancels_queued_and_flags_running(client: AsyncClient, architect, ready, solver, app) -> None:  # noqa: ANN001
    """202; queued become cancelled at once, running get cancel_requested."""
    s = await _study(client, architect, ready, (0, 90))
    running = s["jobs"][0]["id"]
    await sql(app, "UPDATE jobs SET status='running' WHERE id=:j", j=running)
    r = await client.post(f"{URL}/{s['id']}/cancel", headers=architect.headers)
    by = {j["id"]: j for j in r.json()["jobs"]}
    other = next(i for i in by if i != running)
    assert r.status_code == 202
    assert by[running]["status"] == "running" and by[running]["cancel_requested"] is True
    assert by[other]["status"] == "cancelled" and by[other]["finished_at"]


async def test_study_privacy_and_roles(client: AsyncClient, architect, other_architect, reviewer, ready, solver) -> None:  # noqa: ANN001
    """Foreign = missing (404 bytes), reviewer reads but cannot cancel, 401 anonymous."""
    s = await _study(client, architect, ready)
    await client.put(f"/api/v1/projects/{ready['project_id']}/shares/{reviewer.id}", headers=architect.headers)
    foreign = await client.get(f"{URL}/{s['id']}", headers=other_architect.headers)
    missing = await client.get(f"{URL}/00000000-0000-4000-8000-0000000000aa", headers=other_architect.headers)
    seen = await client.get(f"{URL}/{s['id']}", headers=reviewer.headers)
    denied = await client.post(f"{URL}/{s['id']}/cancel", headers=reviewer.headers)
    foreign_cancel = await client.post(f"{URL}/{s['id']}/cancel", headers=other_architect.headers)
    listing = await client.get(f"/api/v1/projects/{ready['project_id']}/simulations", headers=other_architect.headers)
    assert foreign.status_code == missing.status_code == 404 and foreign.content == missing.content
    assert foreign.json()["code"] == "study_not_found" and foreign_cancel.status_code == 404
    assert seen.status_code == 200 and denied.status_code == 403 and listing.status_code == 404
    assert (await client.get(f"{URL}/{s['id']}")).status_code == 401
