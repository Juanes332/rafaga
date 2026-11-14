"""Tile proxy endpoint."""

import os
import time
from pathlib import Path

import httpx
import respx
from httpx import AsyncClient

from app.configs.config import get_settings

PNG = b"\x89PNG\r\n\x1a\nfake"
URL = "https://tile.openstreetmap.org/3/2/1.png"


def _root() -> Path:
    return Path(get_settings().data_dir) / "cache" / "tiles"


async def test_tile_fetched_with_user_agent_then_served_from_cache(client: AsyncClient, architect) -> None:
    """Upstream is hit once, with the identifying User-Agent."""
    with respx.mock() as m:
        route = m.get(URL).respond(200, content=PNG, headers={"Cache-Control": "max-age=60"})
        r = await client.get("/api/v1/tiles/3/2/1.png", headers=architect.headers)
        again = await client.get("/api/v1/tiles/3/2/1.png", headers=architect.headers)
    assert r.status_code == 200 and r.headers["content-type"] == "image/png" and r.content == PNG
    assert again.content == PNG and route.call_count == 1
    assert route.calls[0].request.headers["user-agent"] == get_settings().tile_user_agent
    assert (_root() / "3" / "2" / "1.png").exists()


async def test_tile_validation_and_auth(client: AsyncClient, architect) -> None:
    """z outside 0-19 or x/y outside 2^z is 422; anonymous is 401."""
    for path in ("/20/0/0.png", "/3/8/0.png", "/3/0/8.png", "/3/-1/0.png", "/a/0/0.png"):
        r = await client.get("/api/v1/tiles" + path, headers=architect.headers)
        assert r.status_code == 422 and r.json()["code"] == "validation_error", path
    assert (await client.get("/api/v1/tiles/3/2/1.png")).status_code == 401


async def test_offline_cache_miss_is_503(client: AsyncClient, architect) -> None:
    """No upstream and no cache is tile_unavailable."""
    with respx.mock() as m:
        m.get(URL).mock(side_effect=httpx.ConnectError("off"))
        r = await client.get("/api/v1/tiles/3/2/1.png", headers=architect.headers)
    assert r.status_code == 503 and r.json()["code"] == "tile_unavailable"


async def test_stale_tile_served_when_upstream_fails(client: AsyncClient, architect) -> None:
    """An expired tile beats an offline upstream."""
    with respx.mock() as m:
        m.get(URL).respond(200, content=PNG)
        await client.get("/api/v1/tiles/3/2/1.png", headers=architect.headers)
        meta = _root() / "3" / "2" / "1.json"
        meta.write_text('{"expires": 1}')
        m.get(URL).mock(side_effect=httpx.ConnectError("off"))
        r = await client.get("/api/v1/tiles/3/2/1.png", headers=architect.headers)
    assert r.status_code == 200 and r.content == PNG


async def test_lru_eviction_removes_oldest_beyond_cap(client: AsyncClient, architect, monkeypatch) -> None:
    """With a 1 MB cap, the least recently used tiles go first."""
    monkeypatch.setenv("TILE_CACHE_MAX_MB", "1")
    get_settings.cache_clear()
    big = b"x" * 600_000
    with respx.mock() as m:
        for x in range(3):
            m.get(f"https://tile.openstreetmap.org/3/{x}/0.png").respond(200, content=big)
        for x in range(3):
            await client.get(f"/api/v1/tiles/3/{x}/0.png", headers=architect.headers)
            old = time.time() - 100 + x
            os.utime(_root() / "3" / str(x) / "0.png", (old, old))
    left = sorted(p.parent.name for p in _root().rglob("*.png"))
    assert left == ["2"]


async def test_tiles_use_their_own_budget(client: AsyncClient, architect, monkeypatch) -> None:
    """Principal tile budget answers 429 with Retry-After when spent."""
    monkeypatch.setenv("RATE_LIMIT_TILES_PER_MINUTE", "2")
    get_settings.cache_clear()
    with respx.mock() as m:
        m.get(URL).respond(200, content=PNG)
        codes = [(await client.get("/api/v1/tiles/3/2/1.png", headers=architect.headers)) for _ in range(4)]
    assert [c.status_code for c in codes][:2] == [200, 200] and codes[-1].status_code == 429
    assert "retry-after" in codes[-1].headers
