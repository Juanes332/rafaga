"""Users endpoints (architect only)."""

from httpx import AsyncClient


async def test_architect_lists_users(client: AsyncClient, architect) -> None:  # noqa: ANN001
    """The listing exposes id, email, role and created_at only."""
    r = await client.get("/api/v1/users", headers=architect.headers)
    assert r.status_code == 200
    assert set(r.json()[0]) == {"id", "email", "role", "created_at"}


async def test_reviewer_cannot_list_users(client: AsyncClient, reviewer) -> None:  # noqa: ANN001
    """A reviewer gets 403 forbidden."""
    r = await client.get("/api/v1/users", headers=reviewer.headers)
    assert r.status_code == 403 and r.json()["code"] == "forbidden"


async def test_users_require_authentication(client: AsyncClient) -> None:
    """Without a token the list answers 401."""
    assert (await client.get("/api/v1/users")).status_code == 401


async def test_create_user_then_duplicate_is_409(client: AsyncClient, architect) -> None:  # noqa: ANN001
    """A second user with the same email conflicts, case-insensitively."""
    body = {"email": "New@Rafaga.test", "password": "long-enough-pw", "role": "reviewer"}
    first = await client.post("/api/v1/users", headers=architect.headers, json=body)
    again = await client.post(
        "/api/v1/users", headers=architect.headers, json={**body, "email": "new@rafaga.test"}
    )
    assert first.status_code == 201 and "password" not in first.text
    assert again.status_code == 409 and again.json()["code"] == "email_taken"


async def test_create_user_short_password_is_422(client: AsyncClient, architect) -> None:  # noqa: ANN001
    """Short passwords carry the password_too_short code."""
    r = await client.post(
        "/api/v1/users", headers=architect.headers,
        json={"email": "a@b.test", "password": "short", "role": "reviewer"},
    )
    assert r.status_code == 422 and r.json()["code"] == "password_too_short"


async def test_delete_user_removes_shares_and_self_delete_is_409(
    client: AsyncClient, architect, reviewer, project
) -> None:  # noqa: ANN001
    """Deleting another user is 204 and drops shares; oneself is 409."""
    pid = project["id"]
    await client.put(f"/api/v1/projects/{pid}/shares/{reviewer.id}", headers=architect.headers)
    gone = await client.delete(f"/api/v1/users/{reviewer.id}", headers=architect.headers)
    shares = await client.get(f"/api/v1/projects/{pid}/shares", headers=architect.headers)
    me = await client.delete(f"/api/v1/users/{architect.id}", headers=architect.headers)
    again = await client.delete(f"/api/v1/users/{reviewer.id}", headers=architect.headers)
    assert gone.status_code == 204 and shares.json() == []
    assert me.status_code == 409 and me.json()["code"] == "cannot_delete_self"
    assert again.status_code == 404 and again.json()["code"] == "user_not_found"
    deleted_token = await client.get("/api/v1/auth/me", headers=reviewer.headers)
    assert deleted_token.status_code == 401


async def test_user_responses_never_contain_the_hash(client: AsyncClient, architect) -> None:  # noqa: ANN001
    """The argon2 hash must not appear in any response (ENT-01)."""
    text = (await client.get("/api/v1/users", headers=architect.headers)).text
    text += (await client.get("/api/v1/auth/me", headers=architect.headers)).text
    assert "argon2" not in text and "password_hash" not in text
