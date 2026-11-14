"""POST /geometry/imports: DXF, STL, OBJ, IFC, errors and limits."""

from pathlib import Path

from httpx import AsyncClient
from shapely.geometry import Polygon
from sqlalchemy import text

from tests.routers.geometry.conftest import (
    building,
    dxf_bytes,
    ifc_bytes,
    stepped_stl,
    two_box_obj,
)


def _url(project: dict) -> str:
    return f"/api/v1/projects/{project['id']}/geometry/imports"


async def _post(client, actor, project, name, data, **form):  # noqa: ANN001, ANN202
    return await client.post(_url(project), headers=actor.headers,
                             files={"file": (name, data)}, data=form)


async def test_dxf_import_reads_heights_ignores_open_and_reports(
    client: AsyncClient, architect, project
) -> None:  # noqa: ANN001
    """Layer-number heights, missing_height flag, ignored open polyline."""
    r = await _post(client, architect, project, "site.dxf", dxf_bytes(), center="false")
    body = r.json()
    assert r.status_code == 201
    assert body["buildings_added"] == 2 and body["detected_unit"] == "m"
    assert [i["reason"] for i in body["ignored"]] == ["open_polyline"]
    heights = sorted(b["height_m"] or -1 for b in body["geometry"]["buildings"])
    assert heights == [-1, 12.0]
    assert len(body["missing_height"]) == 1
    assert body["geometry"]["version"] == 2
    assert body["geometry"]["buildings"][0]["footprint"][0][0] == 100


async def test_dxf_unit_detection_converts_centimetres_and_centers(
    client: AsyncClient, architect, project
) -> None:  # noqa: ANN001
    """$INSUNITS=5 means cm: coordinates and heights convert to metres, centred."""
    r = await _post(client, architect, project, "cm.dxf", dxf_bytes(units=5))
    body = r.json()
    assert body["detected_unit"] == "cm"
    xs = [p[0] for b in body["geometry"]["buildings"] for p in b["footprint"]]
    assert abs(min(xs) + max(xs)) < 1e-6 and max(xs) - min(xs) < 1.0
    forced = await _post(client, architect, project, "cm.dxf", dxf_bytes(units=5),
                         unit="mm", mode="replace")
    xs = [p[0] for b in forced.json()["geometry"]["buildings"] for p in b["footprint"]]
    assert max(xs) - min(xs) < 0.1 and len(forced.json()["geometry"]["buildings"]) == 2


async def test_replace_mode_discards_existing_buildings(
    client: AsyncClient, architect, project
) -> None:  # noqa: ANN001
    """append keeps existing buildings, replace drops them."""
    url = f"/api/v1/projects/{project['id']}/geometry"
    await client.put(url, headers=architect.headers,
                     json={"expected_version": 1, "buildings": [building()]})
    appended = await _post(client, architect, project, "a.obj", two_box_obj())
    replaced = await _post(client, architect, project, "a.obj", two_box_obj(), mode="replace")
    assert len(appended.json()["geometry"]["buildings"]) == 3
    assert len(replaced.json()["geometry"]["buildings"]) == 2


async def test_stl_slices_into_stacked_tiers(client: AsyncClient, architect, project) -> None:  # noqa: ANN001
    """A tapering body becomes one building with shrinking 3 m tiers."""
    r = await _post(client, architect, project, "step.stl", stepped_stl())
    b = r.json()["geometry"]["buildings"][0]
    assert r.status_code == 201 and r.json()["buildings_added"] == 1
    assert abs(b["height_m"] - 12) < 1e-6 and b["source"] == "stl"
    assert [round(t["z_to"]) for t in b["tiers"]] == [3, 6, 9, 12]
    areas = [Polygon(t["footprint"]).area for t in b["tiers"]]
    assert areas == sorted(areas, reverse=True)
    assert r.json()["detected_unit"] == "unknown"
    assert "unit_unknown_assumed_m" in r.json()["warnings"]


async def test_obj_yields_one_building_per_body(client: AsyncClient, architect, project) -> None:  # noqa: ANN001
    """Separate OBJ bodies become separate single-tier buildings."""
    r = await _post(client, architect, project, "two.obj", two_box_obj())
    heights = sorted(round(b["height_m"]) for b in r.json()["geometry"]["buildings"])
    assert heights == [8, 20]
    assert all("tiers" not in b or b["tiers"] is None or len(b["tiers"]) > 1
               for b in r.json()["geometry"]["buildings"])


async def test_ifc_import_builds_a_box_per_building(client: AsyncClient, architect, project) -> None:  # noqa: ANN001
    """IfcBuilding elements collapse into an axis-aligned box."""
    r = await _post(client, architect, project, "m.ifc", ifc_bytes(), center="false")
    b = r.json()["geometry"]["buildings"][0]
    assert r.status_code == 201 and b["name"] == "Torre" and b["source"] == "ifc"
    assert abs(b["height_m"] - 12) < 1e-3
    xs = [p[0] for p in b["footprint"]]
    assert abs(max(xs) - min(xs) - 10) < 1e-3


async def test_corrupt_file_is_422_import_failed_and_project_unchanged(
    client: AsyncClient, architect, project
) -> None:  # noqa: ANN001
    """A corrupt file explains cause and hint and changes nothing."""
    for name in ("bad.dxf", "bad.stl", "bad.ifc"):
        r = await _post(client, architect, project, name, b"garbage\x00\x01 not a model")
        assert r.status_code == 422 and r.json()["code"] == "import_failed", name
        assert r.json()["details"]["cause"] and r.json()["hint"]
    got = await client.get(f"/api/v1/projects/{project['id']}/geometry", headers=architect.headers)
    assert got.json()["version"] == 1 and got.json()["buildings"] == []


async def test_unsupported_extension_is_422(client: AsyncClient, architect, project) -> None:  # noqa: ANN001
    """Unknown extensions answer unsupported_format."""
    r = await _post(client, architect, project, "x.dwg", b"AC1015")
    assert r.status_code == 422 and r.json()["code"] == "unsupported_format"


async def test_oversized_upload_is_413_and_not_persisted(
    client: AsyncClient, architect, project, monkeypatch, app
) -> None:  # noqa: ANN001
    """Over the geometry limit: 413 with the limit, no row, no file."""
    from app.configs.config import get_settings

    monkeypatch.setenv("MAX_UPLOAD_GEOMETRY_MB", "1")
    get_settings.cache_clear()
    r = await _post(client, architect, project, "big.stl", b"0" * (2 * 1024 * 1024))
    assert r.status_code == 413 and r.json()["code"] == "upload_too_large"
    assert r.json()["details"]["limit_mb"] == 1
    async with app.state.session_factory() as s:
        assert (await s.execute(text("SELECT count(*) FROM uploads"))).scalar() == 0


async def test_successful_import_is_persisted_under_uploads(
    client: AsyncClient, architect, project, app
) -> None:  # noqa: ANN001
    """The geometry file lands in uploads/<project>/ with sha256 and size."""
    from app.configs.config import get_settings

    data = dxf_bytes()
    await _post(client, architect, project, "site.dxf", data)
    async with app.state.session_factory() as s:
        row = (await s.execute(text("SELECT path, size_bytes, sha256, kind FROM uploads"))).one()
    assert row.kind == "geometry" and row.size_bytes == len(data) and len(row.sha256) == 64
    assert (Path(get_settings().data_dir) / row.path).read_bytes() == data
    assert row.path.startswith(f"uploads/{project['id']}/")


async def test_import_auth_roles_and_privacy(
    client: AsyncClient, architect, reviewer, other_architect, project
) -> None:  # noqa: ANN001
    """401 anonymous, 404 foreign, 403 shared reviewer, 422 missing file."""
    await client.put(f"/api/v1/projects/{project['id']}/shares/{reviewer.id}", headers=architect.headers)
    files = {"file": ("a.dxf", dxf_bytes())}
    assert (await client.post(_url(project), files=files)).status_code == 401
    assert (await _post(client, other_architect, project, "a.dxf", dxf_bytes())).status_code == 404
    assert (await _post(client, reviewer, project, "a.dxf", dxf_bytes())).status_code == 403
    bad = await client.post(_url(project), headers=architect.headers, data={"mode": "append"})
    assert bad.status_code == 422 and bad.json()["code"] == "validation_error"
