"""Export endpoints."""

from pathlib import Path

from httpx import AsyncClient
from sqlalchemy import text

from app.configs.config import get_settings
from app.services.comfort.lawson_service import DEFAULT_LAWSON, lawson_hash
from tests.routers.comfort.test_comfort_router import TEMPLATE

MISSING = "00000000-0000-4000-8000-0000000000ff"
DISCLAIMER = "Herramienta de anteproyecto: compara alternativas, no sustituye un ensayo en túnel de viento."


async def _result(fs, project, actor, **kw):  # noqa: ANN001, ANN202
    study = await fs.study(project["id"], actor.id, template=kw.pop("template", None))
    return study, await fs.result(project["id"], actor.id, study, **kw)


async def test_create_export_enqueues_render_job(client: AsyncClient, fake_solver, project, architect, app) -> None:  # noqa: ANN001
    """POST /exports returns 202 and inserts export + light render job."""
    _, res = await _result(fake_solver, project, architect)
    r = await client.post("/api/v1/exports", headers=architect.headers,
                          json={"result_id": res["id"], "layer": "k"})
    assert r.status_code == 202
    eid = r.json()["export_id"]
    async with app.state.session_factory() as s:
        job = (await s.execute(text(
            "SELECT lane, priority, kind, payload FROM jobs WHERE kind='render'"))).one()
        layer = (await s.execute(text("SELECT layer, file FROM exports WHERE id=:i"), {"i": eid})).one()
    lane, prio, kind, p = job
    assert (lane, prio) == ("light", 10) and layer == ("k", None)
    assert p["job_kind"] == "render" and p["export_id"] == eid and p["dpi"] == 300
    assert p["file_name"] == f"{eid}.png" and p["output_dir"] == f"exports/{architect.id}"
    assert p["result_dir"] == res["dir"] and p["layer"] == "k" and p["comfort_dir"] is None
    assert p["labels"]["disclaimer"] == DISCLAIMER and p["labels"]["project_name"] == "P"
    assert p["labels"]["alternative_a"] == "Caso base"
    assert p["labels"]["wind"] == "Viento del 270° (O), U10 = 10,0 m/s"
    assert p["thresholds"] == {"k_accel": 1.2, "k_stagnation": 0.3, "dk_reduction": -0.1}
    assert p["output_grid"]["frame"] == "plan" and "scene" in p


async def test_export_validation(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """dpi under 300, bad layer, delta_k without compare id are 422; 401 anon."""
    _, res = await _result(fake_solver, project, architect)
    url, h = "/api/v1/exports", architect.headers
    for body in ({"result_id": res["id"], "layer": "k", "dpi": 200},
                 {"result_id": res["id"], "layer": "bad"},
                 {"result_id": res["id"], "layer": "delta_k"}):
        assert (await client.post(url, headers=h, json=body)).status_code == 422
    assert (await client.post(url, json={"result_id": res["id"], "layer": "k"})).status_code == 401


async def test_export_missing_or_foreign_result_is_409_results_missing(client: AsyncClient, fake_solver, project, architect, other_architect) -> None:  # noqa: ANN001
    """Missing and foreign ids answer identically."""
    _, res = await _result(fake_solver, project, architect)
    h = other_architect.headers
    a = await client.post("/api/v1/exports", headers=h, json={"result_id": res["id"], "layer": "k"})
    b = await client.post("/api/v1/exports", headers=h, json={"result_id": MISSING, "layer": "k"})
    assert a.status_code == 409 and a.content == b.content and a.json()["code"] == "results_missing"


async def test_delta_k_incomparable_is_422(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """compare_result_id must be comparable; comparable ones enqueue."""
    _, a = await _result(fake_solver, project, architect)
    _, bad = await _result(fake_solver, project, architect, direction=90.0)
    _, ok = await _result(fake_solver, project, architect)
    body = {"result_id": a["id"], "layer": "delta_k"}
    r = await client.post("/api/v1/exports", headers=architect.headers, json={**body, "compare_result_id": bad["id"]})
    g = await client.post("/api/v1/exports", headers=architect.headers, json={**body, "compare_result_id": ok["id"]})
    assert r.status_code == 422 and r.json()["code"] == "results_incomparable"
    assert g.status_code == 202


async def test_lawson_export_needs_comfort_dir(client: AsyncClient, fake_solver, project, architect, app) -> None:  # noqa: ANN001
    """lawson without a comfort result is 409; with one it carries comfort_dir."""
    study, res = await _result(fake_solver, project, architect, template=TEMPLATE)
    body = {"result_id": res["id"], "layer": "lawson"}
    no = await client.post("/api/v1/exports", headers=architect.headers, json=body)
    job = await fake_solver.job(project["id"], architect.id, study, kind="aggregate", lane="light")
    await fake_solver.comfort(study, job, lawson_hash(DEFAULT_LAWSON, 0.25, "era5:synthetic"))
    yes = await client.post("/api/v1/exports", headers=architect.headers, json=body)
    assert no.status_code == 409 and yes.status_code == 202
    async with app.state.session_factory() as s:
        p = (await s.execute(text("SELECT payload FROM jobs WHERE kind='render'"))).scalar()
    assert p["comfort_dir"] == "results/x"


async def test_reviewer_cannot_export(client: AsyncClient, fake_solver, project, architect, reviewer) -> None:  # noqa: ANN001
    """Launching a job is a write: shared reviewers get 403."""
    _, res = await _result(fake_solver, project, architect)
    await client.put(f"/api/v1/projects/{project['id']}/shares/{reviewer.id}", headers=architect.headers)
    r = await client.post("/api/v1/exports", headers=reviewer.headers, json={"result_id": res["id"], "layer": "k"})
    assert r.status_code == 403 and r.json()["code"] == "forbidden"


async def test_export_status_and_file_lifecycle(client: AsyncClient, fake_solver, project, architect, other_architect, app) -> None:  # noqa: ANN001
    """Status maps the job; the file is 409 until the solver sets it."""
    _, res = await _result(fake_solver, project, architect)
    eid = (await client.post("/api/v1/exports", headers=architect.headers,
                             json={"result_id": res["id"], "layer": "k"})).json()["export_id"]
    st = await client.get(f"/api/v1/exports/{eid}", headers=architect.headers)
    assert st.json() == {"id": eid, "status": "queued", "progress": 0.0, "error": None, "file_ready": False}
    nr = await client.get(f"/api/v1/exports/{eid}/file", headers=architect.headers)
    assert nr.status_code == 409 and nr.json()["code"] == "export_not_ready"
    rel = f"exports/{architect.id}/{eid}.png"
    path = Path(get_settings().data_dir) / rel
    path.parent.mkdir(parents=True)
    path.write_bytes(b"\x89PNGdata")
    async with app.state.session_factory() as s:
        await s.execute(text("UPDATE exports SET file=:f WHERE id=:i"), {"f": rel, "i": eid})
        await s.execute(text("UPDATE jobs SET status='completed', progress=1 WHERE kind='render'"))
        await s.commit()
    ok = await client.get(f"/api/v1/exports/{eid}/file", headers=architect.headers)
    assert ok.status_code == 200 and ok.headers["content-type"] == "image/png"
    assert "attachment" in ok.headers["content-disposition"] and ok.content == b"\x89PNGdata"
    assert (await client.get(f"/api/v1/exports/{eid}", headers=architect.headers)).json()["file_ready"] is True
    f = await client.get(f"/api/v1/exports/{eid}", headers=other_architect.headers)
    m = await client.get(f"/api/v1/exports/{MISSING}", headers=other_architect.headers)
    assert f.status_code == 404 and f.content == m.content and f.json()["code"] == "export_not_found"


async def test_failed_export_exposes_error(client: AsyncClient, fake_solver, project, architect, app) -> None:  # noqa: ANN001
    """A failed render job is surfaced as error{code,message}."""
    _, res = await _result(fake_solver, project, architect)
    eid = (await client.post("/api/v1/exports", headers=architect.headers,
                             json={"result_id": res["id"], "layer": "k"})).json()["export_id"]
    async with app.state.session_factory() as s:
        await s.execute(text("UPDATE jobs SET status='failed', error_code='io_error', error_message='disk' WHERE kind='render'"))
        await s.commit()
    b = (await client.get(f"/api/v1/exports/{eid}", headers=architect.headers)).json()
    assert b["status"] == "failed" and b["error"]["code"] == "io_error"
