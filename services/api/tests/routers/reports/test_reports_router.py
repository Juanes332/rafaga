"""Report endpoints."""

from pathlib import Path

from httpx import AsyncClient
from sqlalchemy import text

from app.configs.config import get_settings
from tests.routers.comfort.test_comfort_router import TEMPLATE

MISSING = "00000000-0000-4000-8000-0000000000ab"


async def _study(fs, project, actor, **kw):  # noqa: ANN001, ANN202
    study = await fs.study(project["id"], actor.id, **kw)
    res = await fs.result(project["id"], actor.id, study)
    return study, res


async def test_create_report_snapshots_and_versions(client: AsyncClient, fake_solver, project, architect, app) -> None:  # noqa: ANN001
    """202, light report job, version increments, payload snapshot."""
    study, res = await _study(fake_solver, project, architect)
    url = f"/api/v1/projects/{project['id']}/reports"
    r1 = await client.post(url, headers=architect.headers, json={"study_ids": [study]})
    r2 = await client.post(url, headers=architect.headers, json={"study_ids": [study], "baseline_study_id": study})
    assert r1.status_code == r2.status_code == 202
    async with app.state.session_factory() as s:
        vers = (await s.execute(text("SELECT version FROM reports ORDER BY version"))).scalars().all()
        job = (await s.execute(text(
            "SELECT lane, priority, payload FROM jobs WHERE kind='report' ORDER BY created_at LIMIT 1"))).one()
    assert vers == [1, 2]
    lane, prio, p = job
    assert (lane, prio) == ("light", 10)
    assert p["job_kind"] == "report" and p["version"] == 1 and p["file_name"] == "rafaga-p-v1.pdf"
    assert p["output_dir"] == f"reports/{project['id']}" and p["report_id"] == r1.json()["report_id"]
    snap = p["snapshot"]
    assert snap["project"]["name"] == "P" and snap["project"]["lat"] is None
    assert snap["wind"]["terrain_category"] == "urban" and snap["wind"]["rose"] is None
    st = snap["studies"][0]
    assert st["study_id"] == study and st["alternative_name"] == "Caso base" and st["dx_m"] == 1.0
    assert st["results"][0]["result_dir"] == res["dir"] and st["results"][0]["wind_from_deg"] == 270.0
    assert st["zone_areas"]["zones"][0]["zone"] == "acceleration" and st["comfort_dir"] is None
    assert snap["thresholds"]["k_accel"] == 1.2 and "disclaimer" in snap and snap["app_version"]
    law = snap["lawson"]
    assert law["comfort"][0] == {"class": "A", "key": "sitting", "threshold_ms": 4}
    assert law["uncomfortable_class"] == "E" and {"exceedance", "safety"} <= set(law)


async def test_report_without_completed_results_is_409(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """A study with no results gives results_missing."""
    study = await fake_solver.study(project["id"], architect.id)
    r = await client.post(f"/api/v1/projects/{project['id']}/reports", headers=architect.headers, json={"study_ids": [study]})
    assert r.status_code == 409 and r.json()["code"] == "results_missing"


async def test_report_validation_auth_privacy_roles(client: AsyncClient, fake_solver, project, architect, other_architect, reviewer) -> None:  # noqa: ANN001
    """422 empty list, 401, foreign project 404, reviewer 403."""
    study, _ = await _study(fake_solver, project, architect)
    url = f"/api/v1/projects/{project['id']}/reports"
    assert (await client.post(url, headers=architect.headers, json={"study_ids": []})).status_code == 422
    assert (await client.post(url, json={"study_ids": [study]})).status_code == 401
    f = await client.post(url, headers=other_architect.headers, json={"study_ids": [study]})
    m = await client.post(f"/api/v1/projects/{MISSING}/reports", headers=other_architect.headers, json={"study_ids": [study]})
    assert f.status_code == 404 and f.content == m.content
    await client.put(f"/api/v1/projects/{project['id']}/shares/{reviewer.id}", headers=architect.headers)
    assert (await client.post(url, headers=reviewer.headers, json={"study_ids": [study]})).status_code == 403
    assert (await client.get(url, headers=reviewer.headers)).status_code == 200


async def test_report_includes_comfort_when_available(client: AsyncClient, fake_solver, project, architect, app) -> None:  # noqa: ANN001
    """include_comfort adds comfort_dir and areas."""
    from app.services.comfort.lawson_service import DEFAULT_LAWSON, lawson_hash

    study, _ = await _study(fake_solver, project, architect, template=TEMPLATE)
    job = await fake_solver.job(project["id"], architect.id, study, kind="aggregate", lane="light")
    await fake_solver.comfort(study, job, lawson_hash(DEFAULT_LAWSON, 0.25, "era5:synthetic"))
    await client.post(f"/api/v1/projects/{project['id']}/reports", headers=architect.headers, json={"study_ids": [study]})
    async with app.state.session_factory() as s:
        p = (await s.execute(text("SELECT payload FROM jobs WHERE kind='report'"))).scalar()
    st = p["snapshot"]["studies"][0]
    assert st["comfort_dir"] == "results/x" and st["comfort_areas"]["partial"] is True


async def test_list_status_and_file(client: AsyncClient, fake_solver, project, architect, other_architect, app) -> None:  # noqa: ANN001
    """List, status and the 409-then-200 file lifecycle."""
    study, _ = await _study(fake_solver, project, architect)
    pid = project["id"]
    rid = (await client.post(f"/api/v1/projects/{pid}/reports", headers=architect.headers, json={"study_ids": [study]})).json()["report_id"]
    lst = (await client.get(f"/api/v1/projects/{pid}/reports", headers=architect.headers)).json()
    assert [(x["id"], x["version"], x["status"]) for x in lst] == [(rid, 1, "queued")]
    st = (await client.get(f"/api/v1/reports/{rid}", headers=architect.headers)).json()
    assert st["status"] == "queued" and st["error"] is None and st["version"] == 1
    nr = await client.get(f"/api/v1/reports/{rid}/file", headers=architect.headers)
    assert nr.status_code == 409 and nr.json()["code"] == "report_not_ready"
    rel = f"reports/{pid}/rafaga-p-v1.pdf"
    path = Path(get_settings().data_dir) / rel
    path.parent.mkdir(parents=True)
    path.write_bytes(b"%PDF-1.4")
    async with app.state.session_factory() as s:
        await s.execute(text("UPDATE reports SET file=:f WHERE id=:i"), {"f": rel, "i": rid})
        await s.commit()
    ok = await client.get(f"/api/v1/reports/{rid}/file", headers=architect.headers)
    assert ok.headers["content-type"] == "application/pdf"
    assert 'filename="rafaga-p-v1.pdf"' in ok.headers["content-disposition"]
    f = await client.get(f"/api/v1/reports/{rid}", headers=other_architect.headers)
    m = await client.get(f"/api/v1/reports/{MISSING}", headers=other_architect.headers)
    assert f.status_code == 404 and f.content == m.content and f.json()["code"] == "report_not_found"
