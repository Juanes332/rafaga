"""GET/PUT/validate geometry endpoints."""

import uuid

from httpx import AsyncClient
from sqlalchemy import text

from tests.routers.geometry.conftest import building


async def test_get_returns_empty_v1(client: AsyncClient, architect, geometry_url) -> None:  # noqa: ANN001
    """A new project has version 1 and no buildings."""
    r = await client.get(geometry_url, headers=architect.headers)
    assert r.status_code == 200
    assert r.json() == {"version": 1, "buildings": [], "issues": [], "orphaned_elements": []}


async def test_get_requires_auth_and_hides_foreign(
    client: AsyncClient, other_architect, geometry_url
) -> None:  # noqa: ANN001
    """Anonymous is 401; a foreign project equals a missing one byte for byte."""
    assert (await client.get(geometry_url)).status_code == 401
    foreign = await client.get(geometry_url, headers=other_architect.headers)
    missing = await client.get(
        f"/api/v1/projects/{uuid.uuid4()}/geometry", headers=other_architect.headers
    )
    assert foreign.status_code == missing.status_code == 404
    assert foreign.content == missing.content


async def test_put_bumps_version_and_normalizes_rings(
    client: AsyncClient, architect, geometry_url
) -> None:  # noqa: ANN001
    """PUT returns version+1; closing vertex dropped, ring made CCW."""
    cw_closed = [[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]]
    b = building(cw_closed)
    r = await client.put(geometry_url, headers=architect.headers,
                         json={"expected_version": 1, "buildings": [b]})
    body = r.json()
    assert r.status_code == 200 and body["version"] == 2
    assert body["buildings"][0]["footprint"] == [[10, 0], [10, 10], [0, 10], [0, 0]]
    assert body["issues"] == []
    assert (await client.get(geometry_url, headers=architect.headers)).json()["version"] == 2


async def test_put_stale_version_is_409_version_conflict(
    client: AsyncClient, architect, geometry_url
) -> None:  # noqa: ANN001
    """A stale expected_version never overwrites."""
    ok = {"expected_version": 1, "buildings": [building()]}
    await client.put(geometry_url, headers=architect.headers, json=ok)
    r = await client.put(geometry_url, headers=architect.headers, json=ok)
    assert r.status_code == 409 and r.json()["code"] == "version_conflict"


async def test_put_validation_errors_are_422(client: AsyncClient, architect, geometry_url) -> None:  # noqa: ANN001
    """Malformed buildings answer validation_error."""
    bad = {"expected_version": 1, "buildings": [{"id": "nope", "footprint": [[0, 0]]}]}
    r = await client.put(geometry_url, headers=architect.headers, json=bad)
    assert r.status_code == 422 and r.json()["code"] == "validation_error"


async def test_put_forbidden_for_reviewer_and_foreign_is_404(
    client: AsyncClient, architect, reviewer, other_architect, geometry_url, project
) -> None:  # noqa: ANN001
    """A shared reviewer gets 403; an outsider the opaque 404."""
    await client.put(f"/api/v1/projects/{project['id']}/shares/{reviewer.id}", headers=architect.headers)
    body = {"expected_version": 1, "buildings": []}
    denied = await client.put(geometry_url, headers=reviewer.headers, json=body)
    hidden = await client.put(geometry_url, headers=other_architect.headers, json=body)
    assert denied.status_code == 403 and denied.json()["code"] == "forbidden"
    assert hidden.status_code == 404
    read = await client.get(geometry_url, headers=reviewer.headers)
    assert read.status_code == 200


async def test_put_base_locked_until_confirmed(
    client: AsyncClient, architect, geometry_url, project
) -> None:  # noqa: ANN001
    """With a derived alternative, the base needs confirm_base_change."""
    # The alternatives router belongs to another batch: insert directly.
    from tests.routers.geometry.helpers import add_alternative

    await add_alternative(client, project["id"])
    body = {"expected_version": 1, "buildings": [building()]}
    locked = await client.put(geometry_url, headers=architect.headers, json=body)
    forced = await client.put(geometry_url, headers=architect.headers,
                              json={**body, "confirm_base_change": True})
    assert locked.status_code == 409 and locked.json()["code"] == "base_locked"
    assert forced.status_code == 200


async def test_put_reports_orphaned_elements(
    client: AsyncClient, architect, geometry_url, project, app
) -> None:  # noqa: ANN001
    """Elements whose building or edge vanished are listed."""
    keep, drop = building(), building()
    first = await client.put(geometry_url, headers=architect.headers,
                             json={"expected_version": 1, "buildings": [keep, drop]})
    assert first.status_code == 200
    async with app.state.session_factory() as s:
        alt = (await s.execute(text("SELECT id FROM alternatives WHERE project_id=:p"), {"p": project["id"]})).scalar()
        ids = []
        for bid, edge in ((keep["id"], 1), (drop["id"], 0), (keep["id"], 9)):
            ids.append((await s.execute(text(
                "INSERT INTO facade_elements (alternative_id,building_id,edge_index,type,params) "
                "VALUES (:a,:b,:e,'screen','{}') RETURNING id"), {"a": alt, "b": bid, "e": edge})).scalar())
        await s.commit()
    r = await client.put(geometry_url, headers=architect.headers,
                         json={"expected_version": 2, "buildings": [keep]})
    assert sorted(r.json()["orphaned_elements"]) == sorted(str(i) for i in ids[1:])


async def test_validate_reports_each_issue_code(client: AsyncClient, architect, geometry_url) -> None:  # noqa: ANN001
    """The validator emits every documented issue code without saving."""
    bow = building([[0, 0], [10, 10], [10, 0], [0, 10]])
    tiny = building([[0, 0], [0.5, 0], [0.5, 0.5], [0, 0.5]])
    nohigh = building([[20, 0], [30, 0], [30, 10], [20, 10]], height=None, missing_height=True)
    tall = building([[40, 0], [50, 0], [50, 10], [40, 10]], height=900)
    a = building([[60, 0], [70, 0], [70, 10], [60, 10]])
    b = building([[65, 0], [75, 0], [75, 10], [65, 10]])
    degenerate = building([[0, 0], [0, 0], [0, 0]])
    r = await client.post(f"{geometry_url}/validate", headers=architect.headers,
                          json={"buildings": [bow, tiny, nohigh, tall, a, b, degenerate]})
    by = {(i["code"], i["building_id"]) for i in r.json()["issues"]}
    assert r.status_code == 200
    assert ("self_intersection", bow["id"]) in by
    assert ("footprint_too_small", tiny["id"]) in by
    assert ("missing_height", nohigh["id"]) in by
    assert ("height_out_of_range", tall["id"]) in by
    assert ("overlap", b["id"]) in by and ("overlap", a["id"]) not in by
    assert ("not_closed", degenerate["id"]) in by
    assert all(i["message_key"].startswith("geometry.issue.") for i in r.json()["issues"])
    assert (await client.get(geometry_url, headers=architect.headers)).json()["buildings"] == []


async def test_validate_uses_stored_buildings_when_none_submitted(
    client: AsyncClient, architect, geometry_url
) -> None:  # noqa: ANN001
    """An empty body validates the stored geometry."""
    await client.put(geometry_url, headers=architect.headers,
                     json={"expected_version": 1, "buildings": [building(height=None, missing_height=True)]})
    r = await client.post(f"{geometry_url}/validate", headers=architect.headers, json={})
    assert [i["code"] for i in r.json()["issues"]] == ["missing_height"]
    assert (await client.post(f"{geometry_url}/validate", json={})).status_code == 401
