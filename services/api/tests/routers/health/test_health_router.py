"""GET /health: public, honest, never throttled."""

from httpx import AsyncClient


async def test_health_is_ok_with_database(client: AsyncClient) -> None:
    """A reachable database answers 200 ok."""
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["db"] == "ok"
    assert r.json()["version"]


async def test_health_reports_degraded_when_database_down(
    monkeypatch, tmp_path
) -> None:  # noqa: ANN001
    """An unreachable database answers 503 degraded."""
    from httpx import ASGITransport

    from app.configs.config import get_settings

    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://x:x@127.0.0.1:1/x")
    get_settings.cache_clear()
    from app.main import create_app

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/health")
    assert r.status_code == 503
    assert r.json()["status"] == "degraded"
    assert r.json()["db"] == "down"
    await app.state.engine.dispose()


async def test_health_is_exempt_from_both_rate_limit_tiers(
    client: AsyncClient, monkeypatch
) -> None:  # noqa: ANN001
    """Probes must never see a 429."""
    from app.configs.config import get_settings

    monkeypatch.setenv("RATE_LIMIT_ANON_PER_MINUTE", "1")
    get_settings.cache_clear()
    codes = {(await client.get("/health")).status_code for _ in range(5)}
    assert codes == {200}
