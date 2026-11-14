"""Auth endpoints: setup, login, me."""

import jwt
from httpx import AsyncClient

from tests.conftest import TEST_JWT_SECRET

CREDS = {"email": "Boss@Rafaga.Test", "password": "long-enough-pw"}


async def test_setup_status_is_true_on_empty_database(client: AsyncClient) -> None:
    """Zero users means setup is needed."""
    r = await client.get("/api/v1/auth/setup-status")
    assert (r.status_code, r.json()) == (200, {"needs_setup": True})


async def test_setup_creates_architect_and_returns_token(client: AsyncClient) -> None:
    """First setup yields 201 and a usable bearer."""
    r = await client.post("/api/v1/auth/setup", json=CREDS)
    body = r.json()
    assert r.status_code == 201
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 720 * 60
    assert body["user"]["role"] == "architect"
    assert body["user"]["email"] == "boss@rafaga.test"
    assert "password" not in r.text and "hash" not in r.text
    me = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert me.status_code == 200 and me.json()["role"] == "architect"
    status = await client.get("/api/v1/auth/setup-status")
    assert status.json() == {"needs_setup": False}


async def test_setup_twice_is_409_setup_already_done(client: AsyncClient) -> None:
    """Setup is closed once any user exists."""
    await client.post("/api/v1/auth/setup", json=CREDS)
    r = await client.post("/api/v1/auth/setup", json=CREDS)
    assert r.status_code == 409 and r.json()["code"] == "setup_already_done"


async def test_setup_short_password_is_422_password_too_short(client: AsyncClient) -> None:
    """Passwords under ten characters are refused with their own code."""
    r = await client.post("/api/v1/auth/setup", json={**CREDS, "password": "short"})
    assert r.status_code == 422 and r.json()["code"] == "password_too_short"


async def test_setup_malformed_payload_is_422_validation_error(client: AsyncClient) -> None:
    """A missing field is a validation error, not a domain one."""
    r = await client.post("/api/v1/auth/setup", json={"email": "nope"})
    assert r.status_code == 422 and r.json()["code"] == "validation_error"


async def test_login_returns_jwt_with_sub_and_role(client: AsyncClient) -> None:
    """The JWT carries the user id as sub and the role claim."""
    setup = (await client.post("/api/v1/auth/setup", json=CREDS)).json()
    r = await client.post("/api/v1/auth/login", json=CREDS)
    claims = jwt.decode(r.json()["access_token"], TEST_JWT_SECRET, algorithms=["HS256"])
    assert r.status_code == 200
    assert claims["sub"] == setup["user"]["id"] and claims["role"] == "architect"


async def test_login_failures_share_one_body(client: AsyncClient) -> None:
    """Unknown email and wrong password are indistinguishable."""
    await client.post("/api/v1/auth/setup", json=CREDS)
    wrong = await client.post("/api/v1/auth/login", json={**CREDS, "password": "bad-password!"})
    unknown = await client.post(
        "/api/v1/auth/login", json={"email": "who@rafaga.test", "password": "bad-password!"}
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.content == unknown.content
    assert wrong.json()["code"] == "invalid_credentials"


async def test_login_eleventh_attempt_is_429_with_retry_after(
    client: AsyncClient, monkeypatch
) -> None:  # noqa: ANN001
    """The login budget is 10 per minute per address."""
    from app.configs.config import get_settings

    monkeypatch.setenv("RATE_LIMIT_LOGIN_PER_MINUTE", "10")
    get_settings.cache_clear()
    bad = {"email": "x@rafaga.test", "password": "whatever"}
    codes = [(await client.post("/api/v1/auth/login", json=bad)).status_code for _ in range(11)]
    assert codes == [401] * 10 + [429]
    last = await client.post("/api/v1/auth/login", json=bad)
    assert int(last.headers["Retry-After"]) >= 1 and last.json()["code"] == "rate_limited"


async def test_me_requires_a_valid_token(client: AsyncClient) -> None:
    """No token, junk token and expired token all answer 401."""
    expired = jwt.encode({"sub": "x", "exp": 1}, TEST_JWT_SECRET, algorithm="HS256")
    for headers in ({}, {"Authorization": "Bearer junk"}, {"Authorization": f"Bearer {expired}"}):
        r = await client.get("/api/v1/auth/me", headers=headers)
        assert r.status_code == 401
