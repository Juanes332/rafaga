"""System status endpoint."""

from httpx import AsyncClient
from sqlalchemy import text


async def test_status_offline_without_solver(client: AsyncClient, architect) -> None:  # noqa: ANN001
    """No solver row means offline."""
    r = await client.get("/api/v1/system/status", headers=architect.headers)
    assert r.status_code == 200
    assert r.json() == {"api": "ok", "db": "ok", "solver": {"online": False, "device": None, "gpu_name": None, "vram_total_bytes": None, "ram_budget_bytes": None, "cpu_cores": None, "mlups_2d": None, "mlups_3d": None, "heartbeat_at": None}}


async def _node(app, age: str) -> None:  # noqa: ANN001
    async with app.state.session_factory() as s:
        await s.execute(text(
            "INSERT INTO solver_nodes VALUES ('w1','gpu','GPU X',8000000000,7000000000,"
            "32000000000,19000000000,16,50.5,40.5,'1',now(), now() - CAST(:a AS interval))"), {"a": age})
        await s.commit()


async def test_status_online_with_fresh_heartbeat(client: AsyncClient, architect, app) -> None:  # noqa: ANN001
    """A heartbeat under 30 s old is online and carries capabilities."""
    await _node(app, "5 seconds")
    s = (await client.get("/api/v1/system/status", headers=architect.headers)).json()["solver"]
    assert s["online"] is True and s["device"] == "gpu" and s["cpu_cores"] == 16


async def test_status_offline_with_stale_heartbeat(client: AsyncClient, architect, app) -> None:  # noqa: ANN001
    """A heartbeat older than 30 s is offline."""
    await _node(app, "31 seconds")
    s = (await client.get("/api/v1/system/status", headers=architect.headers)).json()["solver"]
    assert s["online"] is False


async def test_status_requires_auth(client: AsyncClient) -> None:  # noqa: ANN001
    """No token is 401."""
    assert (await client.get("/api/v1/system/status")).status_code == 401
