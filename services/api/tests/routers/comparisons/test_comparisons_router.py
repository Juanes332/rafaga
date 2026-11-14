"""Comparison endpoints."""

import numpy as np
from httpx import AsyncClient

from tests.routers.comfort.test_comfort_router import SECTORS, TEMPLATE  # noqa: F401
from app.services.comfort.lawson_service import DEFAULT_LAWSON, lawson_hash

H = "/api/v1/comparisons"
MISSING = "00000000-0000-4000-8000-0000000000ee"


async def _pair(fs, project, actor, ka=None, kb=None, **kb_kw):  # noqa: ANN001, ANN202
    s1 = await fs.study(project["id"], actor.id)
    s2 = await fs.study(project["id"], actor.id)
    a = await fs.result(project["id"], actor.id, s1, k=ka)
    b = await fs.result(project["id"], actor.id, s2, k=kb, **kb_kw)
    return a, b


async def test_check_comparable(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """Same grid/direction/dx/z0 are comparable."""
    a, b = await _pair(fake_solver, project, architect)
    r = await client.get(f"{H}/check?a={a['id']}&b={b['id']}", headers=architect.headers)
    assert r.status_code == 200 and r.json()["comparable"] is True


async def test_check_reports_differences(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """Different direction and z0 give 422 with itemised differences."""
    a, b = await _pair(fake_solver, project, architect, direction=90.0, z0=0.3)
    r = await client.get(f"{H}/check?a={a['id']}&b={b['id']}", headers=architect.headers)
    diffs = {d["field"]: d for d in r.json()["details"]["differences"]}
    assert r.status_code == 422 and r.json()["code"] == "results_incomparable"
    assert diffs["direction"] == {"field": "direction", "a": 270.0, "b": 90.0}
    assert diffs["z0"]["b"] == 0.3


async def test_check_validation_and_auth_and_privacy(client: AsyncClient, fake_solver, project, architect, other_architect) -> None:  # noqa: ANN001
    """401, 422 missing params, foreign==missing 404."""
    a, b = await _pair(fake_solver, project, architect)
    assert (await client.get(f"{H}/check?a={a['id']}&b={b['id']}")).status_code == 401
    assert (await client.get(f"{H}/check?a={a['id']}", headers=architect.headers)).status_code == 422
    f = await client.get(f"{H}/check?a={a['id']}&b={b['id']}", headers=other_architect.headers)
    m = await client.get(f"{H}/check?a={MISSING}&b={b['id']}", headers=other_architect.headers)
    assert f.status_code == 404 and f.content == m.content


async def test_areas_compute_reduction(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """Reduction counts cells where K_b - K_a < dk_reduction."""
    ka = np.array([[1.5, 1.5, 0.2, np.nan]], dtype="<f4")
    kb = np.array([[1.0, 1.45, 0.2, np.nan]], dtype="<f4")
    a, b = await _pair(fake_solver, project, architect, ka=ka, kb=kb)
    r = await client.get(f"{H}/areas?a={a['id']}&b={b['id']}&dk_reduction=-0.1", headers=architect.headers)
    body = r.json()
    assert r.status_code == 200
    assert body["a"]["zones"][0]["area_m2"] == 2.0 and body["b"]["zones"][0]["area_m2"] == 1.0
    assert body["reduction"] == {"zone": "reduction", "area_m2": 1.0, "percent": 100 / 3}
    assert body["thresholds"] == {"k_accel": 1.2, "k_stagnation": 0.3, "dk_reduction": -0.1}


async def test_areas_incomparable_and_bad_dk(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """Incomparable is 422; positive dk is 422."""
    a, b = await _pair(fake_solver, project, architect, dx=2.0)
    assert (await client.get(f"{H}/areas?a={a['id']}&b={b['id']}", headers=architect.headers)).status_code == 422
    a2, b2 = await _pair(fake_solver, project, architect)
    r = await client.get(f"{H}/areas?a={a2['id']}&b={b2['id']}&dk_reduction=0.5", headers=architect.headers)
    assert r.status_code == 422


async def test_comfort_comparison(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """Two studies return their comfort side by side; manual wind is 409."""
    h = lawson_hash(DEFAULT_LAWSON, 0.25, "era5:synthetic")
    s1 = await fake_solver.study(project["id"], architect.id, template=TEMPLATE)
    s2 = await fake_solver.study(project["id"], architect.id, template=TEMPLATE)
    for s in (s1, s2):
        j = await fake_solver.job(project["id"], architect.id, s, kind="aggregate", lane="light")
        await fake_solver.comfort(s, j, h)
    r = await client.get(f"{H}/comfort?study_a={s1}&study_b={s2}", headers=architect.headers)
    assert r.status_code == 200 and r.json()["a"]["study_id"] == s1 and r.json()["b"]["status"] == "completed"
    s3 = await fake_solver.study(project["id"], architect.id)
    bad = await client.get(f"{H}/comfort?study_a={s1}&study_b={s3}", headers=architect.headers)
    assert bad.status_code == 409 and bad.json()["code"] == "rose_missing"
    vol = await fake_solver.study(project["id"], architect.id, kind="volume3d", template=TEMPLATE)
    inc = await client.get(f"{H}/comfort?study_a={s1}&study_b={vol}", headers=architect.headers)
    assert inc.status_code == 422 and inc.json()["code"] == "results_incomparable"
