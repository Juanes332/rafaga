"""POST /simulations: study, jobs, payloads, transaction and NOTIFY."""

import asyncio
import json
import os
from pathlib import Path

import psycopg
from httpx import AsyncClient

from tests.routers.simulations.conftest import EXAMPLES, set_rose, sql

URL = "/api/v1/simulations"


def body(ready: dict, **extra) -> dict:  # noqa: ANN003
    """Return a valid creation body."""
    return {"alternative_id": ready["alternative_id"], "kind": "plan2d",
            "directions_deg": [270], "dx_m": 1.0, **extra}


async def test_create_queues_one_heavy_job_per_direction(
    client: AsyncClient, architect, ready, solver, app
) -> None:  # noqa: ANN001
    """202 with a queued study and three heavy jobs."""
    r = await client.post(URL, headers=architect.headers,
                          json=body(ready, directions_deg=[0, 90, 270]))
    j = r.json()
    assert r.status_code == 202 and j["status"] == "queued" and len(j["jobs"]) == 3
    assert sorted(x["direction_deg"] for x in j["jobs"]) == [0, 90, 270]
    assert {x["lane"] for x in j["jobs"]} == {"heavy"} and j["directions_deg"] == [0, 90, 270]
    rows = await sql(app, "SELECT priority, status, device_requested FROM jobs")
    assert {tuple(x) for x in rows} == {(0, "queued", "auto")}


async def test_payload_matches_the_contract_example(client: AsyncClient, architect, ready, solver, app) -> None:  # noqa: ANN001
    """The stored payload equals job.plan2d.example.json where ids allow."""
    await client.post(URL, headers=architect.headers, json=body(ready))
    payload = (await sql(app, "SELECT payload FROM jobs"))[0][0]
    example = json.loads((EXAMPLES / "job.plan2d.example.json").read_text())
    for key in ("contract_version", "job_kind", "section", "wind", "grid", "physics",
                "convergence", "device", "memory", "render"):
        assert payload[key] == example[key], key
    assert payload["output_dir"].startswith(f"results/{ready['project_id']}/")
    assert payload["scene"]["schema_version"] == "1.0"


async def test_volume3d_payload_has_3d_grid_and_perturbation(client: AsyncClient, architect, ready, solver, app) -> None:  # noqa: ANN001
    """Volume jobs carry nz, 224 B/node and the 3D convergence block."""
    await sql(app, "UPDATE solver_nodes SET device='gpu', vram_total_bytes=17179869184")
    r = await client.post(URL, headers=architect.headers, json=body(ready, kind="volume3d"))
    assert r.status_code == 202
    payload = (await sql(app, "SELECT payload FROM jobs"))[0][0]
    example = json.loads((EXAMPLES / "job.volume3d.example.json").read_text())
    for key in ("grid", "physics", "convergence", "memory"):
        assert payload[key] == example[key], key


async def test_section_creates_one_job_with_the_line(client: AsyncClient, architect, ready, solver, app) -> None:  # noqa: ANN001
    """section2d: one job, section in the payload, section grid."""
    sec = {"p0": [0, 40], "p1": [0, -40]}
    r = await client.post(URL, headers=architect.headers, json={
        "alternative_id": ready["alternative_id"], "kind": "section2d", "section": sec, "dx_m": 1.0})
    payload = (await sql(app, "SELECT payload FROM jobs"))[0][0]
    assert r.status_code == 202 and len(r.json()["jobs"]) == 1
    assert payload["section"] == sec and payload["grid"]["output"]["frame"] == "section"


async def test_manual_wind_has_no_aggregate_template(client: AsyncClient, architect, ready, solver, app) -> None:  # noqa: ANN001
    """Manual wind stores NULL; omitted directions use the manual one."""
    r = await client.post(URL, headers=architect.headers,
                          json={"alternative_id": ready["alternative_id"], "kind": "plan2d", "dx_m": 1})
    assert r.status_code == 202 and r.json()["directions_deg"] == [270.0]
    assert (await sql(app, "SELECT aggregate_template FROM studies"))[0][0] is None
    assert (await sql(app, "SELECT direction_deg FROM jobs"))[0][0] == 270


async def test_era5_stores_the_aggregate_template(client: AsyncClient, architect, ready, solver, app) -> None:  # noqa: ANN001
    """The template follows contract 3.4 minus result_refs."""
    await set_rose(app, ready["project_id"])
    r = await client.post(URL, headers=architect.headers, json=body(ready, directions_deg=[270, 90]))
    tpl = (await sql(app, "SELECT aggregate_template FROM studies"))[0][0]
    example = json.loads((EXAMPLES / "job.aggregate.example.json").read_text())
    assert set(tpl) == set(example) - {"result_refs"}
    assert tpl["lawson"]["comfort"] == example["lawson"]["comfort"]
    assert [x["threshold_ms"] for x in tpl["lawson"]["safety"]] == [15.0, 20.0]
    assert tpl["lawson"]["uncomfortable_class"] == "E" and tpl["site"] == example["site"]
    assert tpl["output_grid"] == example["output_grid"] and len(tpl["lawson_hash"]) == 64
    assert tpl["rose"]["cache_key"] == "era5:syn:10y" and len(tpl["rose"]["sectors"]) == 16
    assert tpl["output_dir"].endswith(f"aggregate-{tpl['lawson_hash'][:12]}")
    assert abs(r.json()["coverage"] - 0.12 / 0.96) < 1e-9


async def test_era5_without_rose_and_missing_manual_wind(client: AsyncClient, architect, ready, solver, app) -> None:  # noqa: ANN001
    """era5 with no rose is rose_missing; manual without U10 is wind_missing."""
    await sql(app, "UPDATE wind_climates SET source='era5'")
    a = await client.post(URL, headers=architect.headers, json=body(ready))
    await sql(app, "UPDATE wind_climates SET source='manual', manual_u10_ms=NULL")
    b = await client.post(URL, headers=architect.headers, json=body(ready))
    assert (a.status_code, a.json()["code"]) == (409, "rose_missing")
    assert (b.status_code, b.json()["code"]) == (409, "wind_missing")
    assert (await sql(app, "SELECT count(*) FROM studies"))[0][0] == 0


async def test_create_is_rejected_for_missing_prerequisites(client: AsyncClient, architect, ready, solver, app) -> None:  # noqa: ANN001
    """No location 409, invalid geometry 422, directions required 422."""
    await sql(app, "UPDATE geometries SET buildings='[]'")
    geo = await client.post(URL, headers=architect.headers, json=body(ready))
    await sql(app, "UPDATE projects SET lat=NULL")
    loc = await client.post(URL, headers=architect.headers, json=body(ready))
    await sql(app, "UPDATE projects SET lat=1.5")
    await set_rose(app, ready["project_id"])
    await sql(app, "UPDATE geometries SET buildings=CAST(:b AS jsonb)", b=json.dumps(
        [{"id": "x", "footprint": [[0, 0], [1, 0], [1, 1]], "height_m": 3.0}]))
    nodirs = await client.post(URL, headers=architect.headers,
                               json={"alternative_id": ready["alternative_id"], "kind": "plan2d", "dx_m": 1})
    assert (geo.status_code, geo.json()["code"]) == (422, "geometry_invalid")
    assert (loc.status_code, loc.json()["code"]) == (409, "location_missing")
    assert (nodirs.status_code, nodirs.json()["code"]) == (422, "directions_required")


async def test_mesh_too_large_and_auto_coarsen(client: AsyncClient, architect, ready, solver, app) -> None:  # noqa: ANN001
    """Without auto_coarsen 422 with proposed_dx_m; with it the study uses it."""
    await sql(app, "UPDATE solver_nodes SET ram_budget_bytes=560000000")
    bad = await client.post(URL, headers=architect.headers, json=body(ready, dx_m=0.5))
    ok = await client.post(URL, headers=architect.headers, json=body(ready, dx_m=0.5, auto_coarsen=True))
    proposed = bad.json()["details"]["proposed_dx_m"]
    assert (bad.status_code, bad.json()["code"]) == (422, "mesh_too_large") and proposed > 0.5
    assert ok.status_code == 202 and ok.json()["dx_m"] == proposed
    assert (await sql(app, "SELECT auto_coarsened FROM studies"))[0][0] is True


async def test_payload_over_the_limit_is_413(client: AsyncClient, architect, ready, solver, monkeypatch) -> None:  # noqa: ANN001
    """A payload beyond the configured limit is refused before insertion."""
    from app.configs.config import get_settings

    monkeypatch.setenv("MAX_PAYLOAD_MB", "0")
    get_settings.cache_clear()
    r = await client.post(URL, headers=architect.headers, json=body(ready))
    assert (r.status_code, r.json()["code"]) == (413, "payload_too_large")


async def test_create_authorisation(client: AsyncClient, architect, other_architect, reviewer, ready, solver) -> None:  # noqa: ANN001
    """Reviewer 403, foreign alternative = missing 404, anonymous 401, bad body 422."""
    await client.put(f"/api/v1/projects/{ready['project_id']}/shares/{reviewer.id}", headers=architect.headers)
    denied = await client.post(URL, headers=reviewer.headers, json=body(ready))
    foreign = await client.post(URL, headers=other_architect.headers, json=body(ready))
    missing = await client.post(URL, headers=other_architect.headers, json={
        **body(ready), "alternative_id": "00000000-0000-4000-8000-0000000000aa"})
    assert denied.status_code == 403 and denied.json()["code"] == "forbidden"
    assert foreign.status_code == 404 and foreign.content == missing.content
    assert (await client.post(URL, json=body(ready))).status_code == 401
    too_many = await client.post(URL, headers=architect.headers,
                                 json=body(ready, directions_deg=list(range(17))))
    assert too_many.status_code == 422


async def test_insert_notifies_rafaga_jobs(client: AsyncClient, architect, ready, solver, database_url) -> None:  # noqa: ANN001
    """The DB trigger sends NOTIFY rafaga_jobs 'heavy' on enqueue."""
    dsn = database_url.replace("+psycopg", "")
    async with await psycopg.AsyncConnection.connect(dsn, autocommit=True) as conn:
        await conn.execute("LISTEN rafaga_jobs")
        await client.post(URL, headers=architect.headers, json=body(ready))
        got = []
        async for n in conn.notifies(timeout=3, stop_after=1):
            got.append(n.payload)
    assert got == ["heavy"]


async def test_create_with_the_real_scene_service(client: AsyncClient, architect, ready, solver, app) -> None:  # noqa: ANN001
    """Without the fake, the compiled scene lands in the job payload."""
    app.dependency_overrides.clear()
    r = await client.post(URL, headers=architect.headers, json=body(ready))
    payload = (await sql(app, "SELECT payload FROM jobs"))[0][0]
    assert r.status_code == 202
    assert payload["scene"]["schema_version"] == "1.0" and len(payload["scene"]["solids"]) == 1
    assert payload["scene"]["source"]["alternative_id"] == ready["alternative_id"]
