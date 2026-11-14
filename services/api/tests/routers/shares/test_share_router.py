"""Project sharing endpoints."""

from httpx import AsyncClient


async def test_grant_list_and_revoke_share(
    client: AsyncClient, architect, reviewer, project
) -> None:  # noqa: ANN001
    """Grant is idempotent; the reviewer sees then loses the project."""
    url = f"/api/v1/projects/{project['id']}"
    first = await client.put(f"{url}/shares/{reviewer.id}", headers=architect.headers)
    second = await client.put(f"{url}/shares/{reviewer.id}", headers=architect.headers)
    listed = await client.get(f"{url}/shares", headers=architect.headers)
    seen = await client.get(url, headers=reviewer.headers)
    revoked = await client.delete(f"{url}/shares/{reviewer.id}", headers=architect.headers)
    after = await client.get(url, headers=reviewer.headers)
    assert first.status_code == second.status_code == revoked.status_code == 204
    assert [s["user_id"] for s in listed.json()] == [reviewer.id]
    assert seen.status_code == 200 and seen.json()["role_on_project"] == "reviewer"
    assert after.status_code == 404 and after.json()["code"] == "project_not_found"


async def test_share_unknown_user_is_404_user_not_found(
    client: AsyncClient, architect, project
) -> None:  # noqa: ANN001
    """Sharing with a missing user fails with user_not_found."""
    r = await client.put(
        f"/api/v1/projects/{project['id']}/shares/00000000-0000-4000-8000-0000000000bb",
        headers=architect.headers,
    )
    assert r.status_code == 404 and r.json()["code"] == "user_not_found"


async def test_non_owner_cannot_manage_shares(
    client: AsyncClient, other_architect, reviewer, project
) -> None:  # noqa: ANN001
    """A foreign architect gets the opaque project 404."""
    r = await client.put(
        f"/api/v1/projects/{project['id']}/shares/{reviewer.id}", headers=other_architect.headers
    )
    assert r.status_code == 404 and r.json()["code"] == "project_not_found"


async def test_shares_require_authentication(client: AsyncClient, project) -> None:  # noqa: ANN001
    """No token is 401."""
    assert (await client.get(f"/api/v1/projects/{project['id']}/shares")).status_code == 401
