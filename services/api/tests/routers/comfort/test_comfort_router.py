"""Comfort endpoints."""

import json

from httpx import AsyncClient

from app.services.comfort.lawson_service import DEFAULT_LAWSON, lawson_hash

MISSING = "00000000-0000-4000-8000-0000000000dd"
SECTORS = [{"center_deg": 22.5 * i, "frequency": 1 / 16, "weibull_k": 2.0, "weibull_c_ms": 4.0}
           for i in range(16)]
TEMPLATE = {
    "rose": {"cache_key": "era5:synthetic", "calm_fraction": 0.04, "sectors": SECTORS},
    "site": {"z0_m": 1.0, "z0_ref_m": 0.03, "blending_height_m": 60.0, "analysis_height_m": 1.5},
    "lawson": {}, "turbulence_intensity_default": 0.25, "lawson_hash": "x",
    "output_grid": {"frame": "plan", "origin_x": 0, "origin_y": 0, "dx_m": 1.0, "nx": 2, "ny": 2},
}


def current_hash() -> str:
    return lawson_hash(DEFAULT_LAWSON, 0.25, "era5:synthetic")


async def _study(fs, project, actor, template=TEMPLATE):  # noqa: ANN001, ANN202
    study = await fs.study(project["id"], actor.id, template=template)
    res = await fs.result(project["id"], actor.id, study)
    return study, res


async def test_manual_wind_study_is_409_rose_missing(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """No aggregate template means no comfort."""
    study, _ = await _study(fake_solver, project, architect, template=None)
    for method, url in (("get", f"/api/v1/simulations/{study}/comfort"),
                        ("post", f"/api/v1/simulations/{study}/comfort/recompute")):
        r = await getattr(client, method)(url, headers=architect.headers)
        assert r.status_code == 409 and r.json()["code"] == "rose_missing"


async def test_pending_without_comfort_row(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """Without a result or job the status is pending."""
    study, _ = await _study(fake_solver, project, architect)
    r = await client.get(f"/api/v1/simulations/{study}/comfort", headers=architect.headers)
    assert r.status_code == 200
    assert r.json()["status"] == "pending" and r.json()["lawson_hash"] == current_hash()


async def test_completed_comfort_matches_current_lawson_hash(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """The row stored under the current hash is returned with partial flag."""
    study, res = await _study(fake_solver, project, architect)
    job = await fake_solver.job(project["id"], architect.id, study, kind="aggregate", lane="light")
    await fake_solver.comfort(study, job, current_hash())
    b = (await client.get(f"/api/v1/simulations/{study}/comfort", headers=architect.headers)).json()
    assert b["status"] == "completed" and b["partial"] is True and b["coverage"] == 0.9
    assert b["class_areas"][0]["class"] == "A" and b["safety_areas"][0]["class"] == "general_public"
    assert b["image"] == "lawson"


async def test_recompute_enqueues_light_aggregate_job(client: AsyncClient, fake_solver, project, architect, app) -> None:  # noqa: ANN001
    """POST recompute inserts a light-lane aggregate job, once."""
    from sqlalchemy import text

    study, res = await _study(fake_solver, project, architect)
    url = f"/api/v1/simulations/{study}/comfort/recompute"
    r = await client.post(url, headers=architect.headers)
    again = await client.post(url, headers=architect.headers)
    assert r.status_code == again.status_code == 202 and r.json()["status"] == "pending"
    async with app.state.session_factory() as s:
        rows = (await s.execute(text(
            "SELECT lane, priority, status, payload FROM jobs WHERE kind='aggregate'"))).all()
    assert len(rows) == 1
    lane, prio, status, p = rows[0]
    assert (lane, prio, status) == ("light", 10, "queued")
    assert p["job_kind"] == "aggregate" and p["lawson_hash"] == current_hash()
    assert p["output_dir"].endswith(f"aggregate-{current_hash()[:12]}")
    assert p["result_refs"][0]["result_id"] == res["id"] and p["lawson"]["comfort"][0]["class"] == "A"
    assert p["lawson"]["uncomfortable_class"] == "E" and p["rose"]["cache_key"] == "era5:synthetic"


async def test_recompute_returns_200_when_result_exists(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """An existing comfort result under that hash answers 200."""
    study, _ = await _study(fake_solver, project, architect)
    job = await fake_solver.job(project["id"], architect.id, study, kind="aggregate", lane="light")
    await fake_solver.comfort(study, job, current_hash())
    r = await client.post(f"/api/v1/simulations/{study}/comfort/recompute", headers=architect.headers)
    assert r.status_code == 200 and r.json()["status"] == "completed"


async def test_privacy_auth_and_reviewer_rules(client: AsyncClient, fake_solver, project, architect, other_architect, reviewer) -> None:  # noqa: ANN001
    """Foreign==missing, 401 without token, reviewer reads but cannot recompute."""
    study, _ = await _study(fake_solver, project, architect)
    url = f"/api/v1/simulations/{study}/comfort"
    foreign = await client.get(url, headers=other_architect.headers)
    missing = await client.get(f"/api/v1/simulations/{MISSING}/comfort", headers=other_architect.headers)
    assert foreign.status_code == 404 and foreign.content == missing.content
    assert foreign.json()["code"] == "study_not_found"
    assert (await client.get(url)).status_code == 401
    await client.put(f"/api/v1/projects/{project['id']}/shares/{reviewer.id}", headers=architect.headers)
    assert (await client.get(url, headers=reviewer.headers)).status_code == 200
    rc = await client.post(url + "/recompute", headers=reviewer.headers)
    assert rc.status_code == 403 and rc.json()["code"] == "forbidden"
