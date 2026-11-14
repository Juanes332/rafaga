"""Tiles domain: authenticated OSM proxy with disk cache (ADR-09)."""

from pathlib import Path

import httpx
from fastapi import Depends

from app.configs.config import Settings, get_settings
from app.core.errors.geo_errors import TileCoordinateError, TileUnavailableError
from app.services.geo.external_http import get_http_client
from app.services.tiles import tile_cache as cache

MAX_ZOOM = 19


def validate_tile(z: int, x: int, y: int) -> None:
    """Raise unless z is 0-19 and x, y lie within 2^z."""
    if not (0 <= z <= MAX_ZOOM) or not (0 <= x < 2**z) or not (0 <= y < 2**z):
        raise TileCoordinateError()


class TileService:
    """Serve tiles from cache or the configured upstream."""

    def __init__(self, http: httpx.AsyncClient, settings: Settings) -> None:
        """Bind the client and settings."""
        self._http, self._settings = http, settings
        self._root = Path(settings.data_dir) / "cache" / "tiles"

    async def get(self, z: int, x: int, y: int) -> bytes:
        """Return PNG bytes; stale cache beats an upstream failure."""
        validate_tile(z, x, y)
        path = cache.tile_path(self._root, z, x, y)
        cached = cache.read_tile(path)
        if cached and cached[1]:
            return cached[0]
        fetched = await self._fetch(z, x, y)
        if fetched is None:
            if cached:
                return cached[0]
            raise TileUnavailableError()
        data, ttl = fetched
        cache.write_tile(path, data, ttl)
        cache.evict(self._root, self._settings.tile_cache_max_mb * 1024 * 1024)
        return data

    async def _fetch(self, z: int, x: int, y: int) -> tuple[bytes, int] | None:
        """Download one tile, or None when the upstream fails."""
        url = self._settings.tile_url_template.format(z=z, x=x, y=y)
        try:
            resp = await self._http.get(url, headers={"User-Agent": self._settings.tile_user_agent})
            resp.raise_for_status()
        except httpx.HTTPError:
            return None
        return resp.content, cache.parse_ttl(resp.headers.get("cache-control"))


def get_tile_service(
    http: httpx.AsyncClient = Depends(get_http_client),
    settings: Settings = Depends(get_settings),
) -> TileService:
    """Provide the tile service for a request."""
    return TileService(http, settings)
