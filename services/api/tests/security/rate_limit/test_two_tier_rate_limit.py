"""Both rate-limit tiers (skill Rule 3 and ADR-26)."""

import pytest
from httpx import AsyncClient

from app.configs.config import get_settings
from app.security.rate_limit.rate_limiter import client_address_key, principal_key


def _set(monkeypatch: pytest.MonkeyPatch, **kw: int) -> None:
    for k, v in kw.items():
        monkeypatch.setenv(k.upper(), str(v))
    get_settings.cache_clear()


async def test_rotating_junk_credentials_hit_429_once_address_is_spent(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A fresh junk token per request must not mint a fresh budget."""
    _set(monkeypatch, rate_limit_anon_per_minute=3)
    codes = [
        (await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer junk-{i}"})).status_code
        for i in range(5)
    ]
    assert codes == [401, 401, 401, 429, 429]


async def test_429_carries_retry_after_and_error_body(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A throttled answer advertises when to retry in the shared shape."""
    _set(monkeypatch, rate_limit_anon_per_minute=1)
    await client.get("/api/v1/auth/setup-status")
    r = await client.get("/api/v1/auth/setup-status")
    assert r.status_code == 429 and r.json()["code"] == "rate_limited"
    assert int(r.headers["Retry-After"]) >= 1


async def test_principals_have_independent_tier_two_budgets(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, architect, other_architect
) -> None:
    """One principal exhausting its budget does not throttle another."""
    _set(monkeypatch, rate_limit_per_minute=2)
    a = [(await client.get("/api/v1/auth/me", headers=architect.headers)).status_code for _ in range(3)]
    b = (await client.get("/api/v1/auth/me", headers=other_architect.headers)).status_code
    assert a == [200, 200, 429] and b == 200


def test_keys_are_never_credentials() -> None:
    """The address key is the socket address; IPv6 folds to /64."""
    class Req:
        headers = {"Authorization": "Bearer secret", "X-Forwarded-For": "9.9.9.9"}
        client = type("C", (), {"host": "2001:db8::1234"})()

    assert client_address_key(Req(), trust_proxy=False) == "addr:2001:db8::/64"
    assert client_address_key(Req(), trust_proxy=True) == "addr:9.9.9.9"
    Req.client = type("C", (), {"host": "::ffff:203.0.113.9"})()
    assert client_address_key(Req(), trust_proxy=False) == "addr:203.0.113.9"


def test_principal_key_requires_a_guard() -> None:
    """Tier 2 refuses to run without an authenticated principal."""
    class Req:
        state = type("S", (), {})()

    with pytest.raises(LookupError):
        principal_key(Req())
