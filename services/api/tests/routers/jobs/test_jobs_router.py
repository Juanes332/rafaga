"""Jobs endpoints: read, cancel, retry."""

from httpx import AsyncClient

from tests.routers.simulations.conftest import sql

URL = "/api/v1/jobs"


async def _job(client, architect, ready) -> str:  # noqa: ANN001
    r = await client.post("/api/v1/simulations", headers=architect.headers, json={
        "alternative_id": ready["alternative_id"], "kind": "plan2d",
        "directions_deg": [270], "dx_m": 1.0})
    return r.json()["jobs"][0]["id"]


async def test_get_job_any_lane(client: AsyncClient, architect, ready, solver, app) -> None:  # noqa: ANN001
    """A heavy job and a light job are both readable."""
    job = await _job(client, architect, ready)
    light = (await sql(app, "INSERT INTO jobs (project_id, owner_id, kind, lane, priority, payload) "
                       "SELECT project_id, owner_id, 'render', 'light', 10, '{}' FROM jobs "
                       "RETURNING id"))[0][0]
    a = await client.get(f"{URL}/{job}", headers=architect.headers)
    b = await client.get(f"{URL}/{light}", headers=architect.headers)
    assert a.status_code == b.status_code == 200
    assert (a.json()["lane"], b.json()["lane"]) == ("heavy", "light")
    assert a.json()["resumable"] is False and a.json()["error"] is None


async def test_cancel_queued_running_and_finished(client: AsyncClient, architect, ready, solver, app) -> None:  # noqa: ANN001
    """Queued -> cancelled, running -> flag, finished -> 409."""
    q, r, f = [await _job(client, architect, ready) for _ in range(3)]
    await sql(app, "UPDATE jobs SET status='running' WHERE id=:j", j=r)
    await sql(app, "UPDATE jobs SET status='completed' WHERE id=:j", j=f)
    cq = await client.post(f"{URL}/{q}/cancel", headers=architect.headers)
    cr = await client.post(f"{URL}/{r}/cancel", headers=architect.headers)
    cf = await client.post(f"{URL}/{f}/cancel", headers=architect.headers)
    assert cq.status_code == cr.status_code == 202 and cq.json()["status"] == "cancelled"
    assert cr.json()["cancel_requested"] is True and cr.json()["status"] == "running"
    assert (cf.status_code, cf.json()["code"]) == (409, "job_not_cancellable")


async def test_retry_only_failed_resumable(client: AsyncClient, architect, ready, solver, app) -> None:  # noqa: ANN001
    """Resumable failed jobs return to queued, attempts kept; others 409."""
    ok, hard, running = [await _job(client, architect, ready) for _ in range(3)]
    await sql(app, "UPDATE jobs SET status='failed', resumable=true, attempts=1, "
              "error_code='worker_restarted', error_message='x', progress=0.5 WHERE id=:j", j=ok)
    await sql(app, "UPDATE jobs SET status='failed', resumable=false WHERE id=:j", j=hard)
    await sql(app, "UPDATE jobs SET status='running' WHERE id=:j", j=running)
    good = await client.post(f"{URL}/{ok}/retry", headers=architect.headers)
    codes = [(await client.post(f"{URL}/{j}/retry", headers=architect.headers)) for j in (hard, running)]
    attempts = (await sql(app, "SELECT attempts FROM jobs WHERE id=:j", j=ok))[0][0]
    assert good.status_code == 202 and good.json()["status"] == "queued"
    assert good.json()["error"] is None and good.json()["progress"] == 0 and attempts == 1
    assert [(c.status_code, c.json()["code"]) for c in codes] == [(409, "job_not_retryable")] * 2


async def test_job_privacy_roles_and_auth(client: AsyncClient, architect, other_architect, reviewer, ready, solver) -> None:  # noqa: ANN001
    """Foreign = missing, reviewer 403 on writes, anonymous 401."""
    job = await _job(client, architect, ready)
    await client.put(f"/api/v1/projects/{ready['project_id']}/shares/{reviewer.id}", headers=architect.headers)
    foreign = await client.get(f"{URL}/{job}", headers=other_architect.headers)
    missing = await client.get(f"{URL}/00000000-0000-4000-8000-0000000000aa", headers=other_architect.headers)
    assert foreign.status_code == 404 and foreign.content == missing.content
    assert foreign.json()["code"] == "job_not_found"
    assert (await client.get(f"{URL}/{job}", headers=reviewer.headers)).status_code == 200
    for verb in ("cancel", "retry"):
        assert (await client.post(f"{URL}/{job}/{verb}", headers=reviewer.headers)).status_code == 403
        assert (await client.post(f"{URL}/{job}/{verb}", headers=other_architect.headers)).status_code == 404
        assert (await client.post(f"{URL}/{job}/{verb}")).status_code == 401
    assert (await client.get(f"{URL}/not-a-uuid", headers=architect.headers)).status_code == 422
