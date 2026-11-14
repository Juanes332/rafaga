"""Background plan endpoints."""

import io
import uuid
from pathlib import Path

from httpx import AsyncClient
from PIL import Image
from sqlalchemy import text

from tests.routers.backgrounds.conftest import pdf_bytes, png_bytes


def _url(project: dict) -> str:
    return f"/api/v1/projects/{project['id']}/backgrounds"


async def _upload(client, actor, project, name="plan.png", data=None):  # noqa: ANN001, ANN202
    return await client.post(_url(project), headers=actor.headers,
                             files={"file": (name, data or png_bytes())})


async def test_upload_png_and_pdf_report_page_count(client: AsyncClient, architect, project) -> None:  # noqa: ANN001
    """PNG has one page, a PDF as many as it holds."""
    png = await _upload(client, architect, project)
    pdf = await _upload(client, architect, project, "plan.pdf", pdf_bytes(2))
    assert png.status_code == pdf.status_code == 201
    assert png.json()["page_count"] == 1 and pdf.json()["page_count"] == 2
    assert pdf.json()["opacity"] == 0.5 and pdf.json()["calibration"] is None
    listed = await client.get(_url(project), headers=architect.headers)
    assert [b["page_count"] for b in listed.json()] == [1, 2]


async def test_upload_rejects_wrong_content_and_extension(client: AsyncClient, architect, project) -> None:  # noqa: ANN001
    """A .png that is not a PNG, or a .txt, is unsupported_format."""
    fake = await _upload(client, architect, project, "x.png", b"not an image at all")
    text_file = await _upload(client, architect, project, "x.txt", b"hello")
    assert fake.status_code == text_file.status_code == 422
    assert fake.json()["code"] == "unsupported_format"


async def test_upload_over_25mb_is_413_with_limit(
    client: AsyncClient, architect, project, monkeypatch, app
) -> None:  # noqa: ANN001
    """Over the image limit answers 413 with the limit and stores nothing."""
    from app.configs.config import get_settings

    monkeypatch.setenv("MAX_UPLOAD_IMAGE_MB", "1")
    get_settings.cache_clear()
    r = await _upload(client, architect, project, "big.png", b"\x89PNG\r\n\x1a\n" + b"0" * 2_100_000)
    assert r.status_code == 413 and r.json()["code"] == "upload_too_large"
    assert r.json()["details"]["limit_mb"] == 1
    async with app.state.session_factory() as s:
        assert (await s.execute(text("SELECT count(*) FROM uploads"))).scalar() == 0


async def test_page_png_rasterizes_within_budget(client: AsyncClient, architect, project) -> None:  # noqa: ANN001
    """Pages come back as PNG no larger than 4096 px on the long side."""
    big = await _upload(client, architect, project, "big.png", png_bytes((6000, 3000)))
    pdf = await _upload(client, architect, project, "p.pdf", pdf_bytes(2))
    r1 = await client.get(f"/api/v1/backgrounds/{big.json()['id']}/pages/1.png", headers=architect.headers)
    r2 = await client.get(f"/api/v1/backgrounds/{pdf.json()['id']}/pages/2.png", headers=architect.headers)
    assert r1.status_code == r2.status_code == 200
    assert r1.headers["content-type"] == "image/png"
    assert max(Image.open(io.BytesIO(r1.content)).size) == 4096
    assert Image.open(io.BytesIO(r2.content)).size[0] > Image.open(io.BytesIO(r2.content)).size[1]


async def test_page_out_of_range_is_404_page_not_found(client: AsyncClient, architect, project) -> None:  # noqa: ANN001
    """Pages beyond the count (or zero) are page_not_found."""
    plan = (await _upload(client, architect, project)).json()
    for page in (2, 0):
        r = await client.get(f"/api/v1/backgrounds/{plan['id']}/pages/{page}.png", headers=architect.headers)
        assert r.status_code == 404 and r.json()["code"] == "page_not_found"


async def test_patch_stores_calibration_and_derives_scale(client: AsyncClient, architect, project) -> None:  # noqa: ANN001
    """metres_per_pixel = distance_m / pixel distance; persisted."""
    plan = (await _upload(client, architect, project)).json()
    cal = {"p1": [0, 0], "p2": [30, 40], "distance_m": 25}
    r = await client.patch(f"/api/v1/backgrounds/{plan['id']}", headers=architect.headers,
                           json={"calibration": cal, "opacity": 0.8,
                                 "transform": {"offset": [1, 2], "rotation_deg": 10, "scale": 2}})
    body = r.json()
    assert r.status_code == 200 and abs(body["metres_per_pixel"] - 0.5) < 1e-9
    assert body["opacity"] == 0.8 and body["transform"]["offset"] == [1, 2]
    again = (await client.get(_url(project), headers=architect.headers)).json()[0]
    assert again["calibration"] == cal


async def test_patch_validation(client: AsyncClient, architect, project) -> None:  # noqa: ANN001
    """distance_m must be positive, opacity within 0..1, page within count."""
    plan = (await _upload(client, architect, project)).json()
    url = f"/api/v1/backgrounds/{plan['id']}"
    bad_cal = await client.patch(url, headers=architect.headers,
                                 json={"calibration": {"p1": [0, 0], "p2": [1, 1], "distance_m": 0}})
    bad_op = await client.patch(url, headers=architect.headers, json={"opacity": 2})
    bad_page = await client.patch(url, headers=architect.headers, json={"page": 3})
    assert bad_cal.status_code == bad_op.status_code == 422
    assert bad_page.status_code == 404 and bad_page.json()["code"] == "page_not_found"


async def test_delete_removes_row_and_file(client: AsyncClient, architect, project, app) -> None:  # noqa: ANN001
    """DELETE drops the plan, the upload row and the file."""
    from app.configs.config import get_settings

    plan = (await _upload(client, architect, project)).json()
    async with app.state.session_factory() as s:
        path = (await s.execute(text("SELECT path FROM uploads"))).scalar()
    assert (Path(get_settings().data_dir) / path).exists()
    r = await client.delete(f"/api/v1/backgrounds/{plan['id']}", headers=architect.headers)
    assert r.status_code == 204 and not (Path(get_settings().data_dir) / path).exists()
    assert (await client.get(_url(project), headers=architect.headers)).json() == []


async def test_plans_are_deleted_with_their_project(client: AsyncClient, architect, project, app) -> None:  # noqa: ANN001
    """Project deletion cascades to plans and uploads."""
    await _upload(client, architect, project)
    await client.delete(f"/api/v1/projects/{project['id']}", headers=architect.headers)
    async with app.state.session_factory() as s:
        assert (await s.execute(text("SELECT count(*) FROM background_plans"))).scalar() == 0


async def test_privacy_auth_and_roles(
    client: AsyncClient, architect, reviewer, other_architect, project
) -> None:  # noqa: ANN001
    """Foreign == missing, anonymous 401, shared reviewer reads but cannot write."""
    plan = (await _upload(client, architect, project)).json()
    await client.put(f"/api/v1/projects/{project['id']}/shares/{reviewer.id}", headers=architect.headers)
    page = f"/api/v1/backgrounds/{plan['id']}/pages/1.png"
    missing = f"/api/v1/backgrounds/{uuid.uuid4()}/pages/1.png"
    foreign = await client.get(page, headers=other_architect.headers)
    absent = await client.get(missing, headers=other_architect.headers)
    assert foreign.status_code == absent.status_code == 404 and foreign.content == absent.content
    assert foreign.json()["code"] == "background_not_found"
    assert (await client.get(page)).status_code == 401
    assert (await client.get(page, headers=reviewer.headers)).status_code == 200
    assert (await client.get(_url(project), headers=reviewer.headers)).status_code == 200
    assert (await _upload(client, reviewer, project)).status_code == 403
    url = f"/api/v1/backgrounds/{plan['id']}"
    assert (await client.patch(url, headers=reviewer.headers, json={"opacity": 0.1})).status_code == 403
    assert (await client.delete(url, headers=reviewer.headers)).status_code == 403
    assert (await client.patch(url, headers=other_architect.headers, json={"opacity": 0.1})).status_code == 404
    assert (await client.delete(url, headers=other_architect.headers)).status_code == 404
    hidden = await _upload(client, other_architect, project)
    assert hidden.status_code == 404 and hidden.json()["code"] == "project_not_found"
