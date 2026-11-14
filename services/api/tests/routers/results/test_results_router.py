"""Results endpoints: metadata, fields, images, zones, viewer3d, download."""

import io
import time

import numpy as np
from httpx import AsyncClient

MISSING = "00000000-0000-4000-8000-0000000000cc"


async def _make(fake_solver, project, architect, **kw):  # noqa: ANN001, ANN202
    study = await fake_solver.study(project["id"], architect.id, kind=kw.get("kind", "plan2d"))
    return await fake_solver.result(project["id"], architect.id, study, **kw)


async def test_result_metadata_is_read_from_the_row(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """GET /results/{id} returns the Result schema."""
    res = await _make(fake_solver, project, architect)
    r = await client.get(f"/api/v1/results/{res['id']}", headers=architect.headers)
    b = r.json()
    assert r.status_code == 200
    assert b["kind"] == "plan2d" and b["direction_deg"] == 270.0 and b["device"] == "cpu"
    assert set(b["stats"]) >= {"k_mean", "k_max", "k_p95"}
    assert b["fields"] == ["K", "ux", "uy", "speed", "mask"]
    assert b["images"] == ["k.png", "speed.png", "zones.png"]
    assert b["output_grid"]["frame"] == "plan" and len(b["comparability_key"]) == 64
    assert b["convergence"]["converged"] is True and "rel_change" in b["convergence"]


async def test_result_warnings_are_exposed_as_codes(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """Solver warnings stored as {code, ref} objects are exposed as their codes."""
    res = await _make(fake_solver, project, architect,
                      warnings=[{"code": "low_reynolds", "ref": "b1"}, "local_mach_spikes"])
    r = await client.get(f"/api/v1/results/{res['id']}", headers=architect.headers)
    assert r.status_code == 200
    assert r.json()["warnings"] == ["low_reynolds", "local_mach_spikes"]


async def test_image_is_served_by_contract_file_name(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """images/k.png (the openapi pattern) streams the PNG."""
    res = await _make(fake_solver, project, architect)
    r = await client.get(f"/api/v1/results/{res['id']}/images/k.png", headers=architect.headers)
    assert r.status_code == 200 and r.content[:8] == b"\x89PNG\r\n\x1a\n"


async def test_result_requires_auth_and_validates_id(client: AsyncClient) -> None:  # noqa: ANN001
    """401 without a token; 422 for a malformed id."""
    assert (await client.get(f"/api/v1/results/{MISSING}")).status_code == 401


async def test_foreign_result_is_byte_identical_to_missing(client: AsyncClient, fake_solver, project, architect, other_architect) -> None:  # noqa: ANN001
    """A foreign result id answers exactly like a random one."""
    res = await _make(fake_solver, project, architect)
    foreign = await client.get(f"/api/v1/results/{res['id']}", headers=other_architect.headers)
    missing = await client.get(f"/api/v1/results/{MISSING}", headers=other_architect.headers)
    assert foreign.status_code == missing.status_code == 404
    assert foreign.content == missing.content
    assert foreign.json()["code"] == "result_not_found"
    for sub in ("zones", "viewer3d", "download?format=npz", "fields/K", "images/k"):
        f = await client.get(f"/api/v1/results/{res['id']}/{sub}", headers=other_architect.headers)
        assert f.status_code == 404 and f.json()["code"] == "result_not_found"


async def test_shared_reviewer_can_read(client: AsyncClient, fake_solver, project, architect, reviewer) -> None:  # noqa: ANN001
    """Reading is allowed through a share."""
    res = await _make(fake_solver, project, architect)
    await client.put(f"/api/v1/projects/{project['id']}/shares/{reviewer.id}", headers=architect.headers)
    r = await client.get(f"/api/v1/results/{res['id']}", headers=reviewer.headers)
    assert r.status_code == 200


async def test_field_streams_raw_float32_with_headers(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """Fields stream raw bytes with shape and dtype headers."""
    k = np.arange(12, dtype="<f4").reshape(3, 4)
    res = await _make(fake_solver, project, architect, k=k)
    r = await client.get(f"/api/v1/results/{res['id']}/fields/K", headers=architect.headers)
    assert r.status_code == 200
    assert r.headers["X-Field-Shape"] == "3,4" and r.headers["X-Field-Dtype"] == "float32"
    assert np.frombuffer(r.content, dtype="<f4").reshape(3, 4).tolist() == k.tolist()
    m = await client.get(f"/api/v1/results/{res['id']}/fields/mask", headers=architect.headers)
    assert m.headers["X-Field-Dtype"] == "uint8"


async def test_unknown_field_and_traversal_are_404(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """Only allow-listed names are served; paths never are."""
    res = await _make(fake_solver, project, architect)
    for name in ("nope", "..%2F..%2Fmanifest.json", "K.f32", "uz"):
        r = await client.get(f"/api/v1/results/{res['id']}/fields/{name}", headers=architect.headers)
        assert r.status_code == 404 and r.json()["code"] == "field_not_found"
    r = await client.get(f"/api/v1/results/{res['id']}/images/..%2Ffields%2FK", headers=architect.headers)
    assert r.status_code == 404 and r.json()["code"] == "image_not_found"


async def test_image_streams_png(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """Preview images stream as PNG."""
    res = await _make(fake_solver, project, architect)
    r = await client.get(f"/api/v1/results/{res['id']}/images/k", headers=architect.headers)
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    assert r.content[:4] == b"\x89PNG"


async def test_zones_compute_areas_with_defaults(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """Acceleration/stagnation areas exclude NaN solids from the fluid area."""
    k = np.array([[0.1, 0.5, 1.3, np.nan], [2.0, 1.0, 0.2, np.nan]], dtype="<f4")
    res = await _make(fake_solver, project, architect, k=k, dx=2.0)
    r = await client.get(f"/api/v1/results/{res['id']}/zones", headers=architect.headers)
    b = r.json()
    zones = {z["zone"]: z for z in b["zones"]}
    assert r.status_code == 200 and b["thresholds"] == {"k_accel": 1.2, "k_stagnation": 0.3}
    assert b["fluid_area_m2"] == 6 * 4.0
    assert zones["acceleration"]["area_m2"] == 8.0 and round(zones["acceleration"]["percent"], 2) == 33.33
    assert zones["stagnation"]["area_m2"] == 8.0


async def test_zones_thresholds_from_query_and_validation(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """Query thresholds override; inverted or non-positive ones are 422."""
    res = await _make(fake_solver, project, architect)
    url = f"/api/v1/results/{res['id']}/zones"
    ok = await client.get(url + "?k_accel=0.5&k_stagnation=0.1", headers=architect.headers)
    bad = await client.get(url + "?k_accel=0.2&k_stagnation=0.5", headers=architect.headers)
    neg = await client.get(url + "?k_accel=-1", headers=architect.headers)
    assert ok.status_code == 200 and ok.json()["thresholds"]["k_accel"] == 0.5
    assert bad.status_code == 422 and neg.status_code == 422


async def test_zones_use_user_settings_row(client: AsyncClient, fake_solver, project, architect, app) -> None:  # noqa: ANN001
    """Defaults come from the caller's user_settings row when present."""
    from sqlalchemy import text

    async with app.state.session_factory() as s:
        await s.execute(text(
            "INSERT INTO user_settings VALUES (:u, CAST(:t AS jsonb), '{}'::jsonb, 0.25, 0.2, 8)"),
            {"u": architect.id, "t": '{"k_accel":1.5,"k_stagnation":0.4,"dk_reduction":-0.1}'})
        await s.commit()
    res = await _make(fake_solver, project, architect)
    b = (await client.get(f"/api/v1/results/{res['id']}/zones", headers=architect.headers)).json()
    assert b["thresholds"] == {"k_accel": 1.5, "k_stagnation": 0.4}


async def test_zones_for_400x300_run_within_two_seconds(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """NFR-05: re-zoning a 400x300 field takes at most 2 s."""
    k = np.random.default_rng(1).uniform(0, 2, (300, 400))
    res = await _make(fake_solver, project, architect, k=k)
    t0 = time.perf_counter()
    r = await client.get(f"/api/v1/results/{res['id']}/zones", headers=architect.headers)
    assert r.status_code == 200 and time.perf_counter() - t0 <= 2.0


async def test_viewer3d_for_volume_and_404_for_plan(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """volume3d returns scene+slices+streamlines; other kinds 404."""
    vol = await _make(fake_solver, project, architect, kind="volume3d", scene={"solids": [1], "porous": []})
    plan = await _make(fake_solver, project, architect)
    r = await client.get(f"/api/v1/results/{vol['id']}/viewer3d", headers=architect.headers)
    b = r.json()
    assert r.status_code == 200 and b["scene"]["solids"] == [1]
    assert b["slices"][0]["name"] == "xz" and b["streamlines"][0][0] == [0, 0, 0]
    n = await client.get(f"/api/v1/results/{plan['id']}/viewer3d", headers=architect.headers)
    assert n.status_code == 404 and n.json()["code"] == "viewer_not_available"


async def test_download_npz_and_csv(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """npz streams the bundle; csv lists fluid cells in plan coordinates."""
    k = np.array([[1.0, np.nan], [2.0, 3.0]], dtype="<f4")
    res = await _make(fake_solver, project, architect, k=k)
    url = f"/api/v1/results/{res['id']}/download"
    z = await client.get(url + "?format=npz", headers=architect.headers)
    assert z.status_code == 200 and "attachment" in z.headers["content-disposition"]
    assert "K" in np.load(io.BytesIO(z.content)).files
    c = await client.get(url + "?format=csv", headers=architect.headers)
    lines = c.text.strip().splitlines()
    assert "attachment" in c.headers["content-disposition"]
    assert lines[0] == "x,y,K,ux,uy,speed" and len(lines) == 4
    assert lines[1].split(",")[:3] == ["-3.5", "-2.5", "1.0"]
    bad = await client.get(url + "?format=zip", headers=architect.headers)
    assert bad.status_code == 422


async def test_every_manifest_image_is_listed_and_served(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """delta and slice_* images in the manifest are listed as <name>.png and streamed."""
    res = await _make(fake_solver, project, architect, kind="volume3d")
    b = (await client.get(f"/api/v1/results/{res['id']}", headers=architect.headers)).json()
    assert {"delta.png", "slice_xz.png"} <= set(b["images"])
    for name in ("delta.png", "slice_xz.png"):
        r = await client.get(f"/api/v1/results/{res['id']}/images/{name}", headers=architect.headers)
        assert r.status_code == 200 and r.content[:4] == b"\x89PNG"


async def test_image_name_outside_the_allow_list_is_not_found(client: AsyncClient, fake_solver, project, architect) -> None:  # noqa: ANN001
    """Names that do not match the contract pattern are 404 even when well formed."""
    res = await _make(fake_solver, project, architect)
    for name in ("Slice_XZ.png", "other.png", "slice_.png.png"):
        r = await client.get(f"/api/v1/results/{res['id']}/images/{name}", headers=architect.headers)
        assert r.status_code == 404 and r.json()["code"] == "image_not_found"
