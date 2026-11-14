"""Geo domain: Open-Meteo geocoding and elevation behind a cache."""

import httpx
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.config import Settings, get_settings
from app.core.database.database import get_session
from app.core.errors.geo_errors import (
    CoordinatesOutOfRangeError,
    ElevationUnavailableError,
    GeocodingUnavailableError,
)
from app.models.geo.geo_schemas import ElevationResponse, GeoResult, TerrainCategory
from app.repositories.geo import external_cache_repository as cache
from app.services.geo.external_http import get_http_client
from app.services.geo.isa_density import isa_density

GEOCODE_TTL_DAYS = 30
ELEVATION_TTL_DAYS = 365
TERRAIN = [
    ("open_sea", 0.0002), ("open", 0.03), ("suburban", 0.3),
    ("urban", 1.0), ("dense_urban", 2.0),
]


def terrain_categories() -> list[TerrainCategory]:
    """Return the five BR-08 categories with urban flagged default."""
    return [TerrainCategory(key=k, label_key=f"terrain.{k}", z0_m=z, default=k == "urban")
            for k, z in TERRAIN]


def check_coordinates(lat: float, lon: float) -> None:
    """Raise when latitude or longitude is out of range."""
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise CoordinatesOutOfRangeError()


def _match(item: dict) -> dict:
    """Map an Open-Meteo geocoding hit to a GeoResult dict."""
    return {"name": item["name"], "admin1": item.get("admin1"),
            "country": item.get("country"), "lat": item["latitude"],
            "lon": item["longitude"], "elevation_m": item.get("elevation")}


class GeoService:
    """Search places and look up elevations, caching every answer."""

    def __init__(self, session: AsyncSession, http: httpx.AsyncClient, settings: Settings) -> None:
        """Bind collaborators."""
        self._session, self._http, self._settings = session, http, settings

    async def search(self, q: str) -> list[GeoResult]:
        """Return up to 10 matches; cached 30 days."""
        key = f"es:{q.strip().lower()}"
        hit = await cache.get_cached(self._session, "geocode", key)
        if hit is None:
            hit = await self._fetch_geocode(q.strip())
            await cache.put_cached(self._session, "geocode", key, hit, GEOCODE_TTL_DAYS)
        return [GeoResult(**r) for r in hit]

    async def _fetch_geocode(self, q: str) -> list[dict]:
        """Call Open-Meteo geocoding."""
        try:
            resp = await self._http.get(
                self._settings.geocoding_url,
                params={"name": q, "count": 10, "language": "es", "format": "json"})
            resp.raise_for_status()
            return [_match(i) for i in resp.json().get("results", [])]
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            raise GeocodingUnavailableError() from exc

    async def elevation_m(self, lat: float, lon: float) -> float:
        """Return elevation for coordinates rounded to 4 decimals."""
        check_coordinates(lat, lon)
        lat, lon = round(lat, 4), round(lon, 4)
        key = f"{lat:.4f},{lon:.4f}"
        hit = await cache.get_cached(self._session, "elevation", key)
        if hit is None:
            hit = await self._fetch_elevation(lat, lon)
            await cache.put_cached(self._session, "elevation", key, hit, ELEVATION_TTL_DAYS)
        return float(hit["elevation_m"])

    async def _fetch_elevation(self, lat: float, lon: float) -> dict:
        """Call Open-Meteo elevation with rounded coordinates only."""
        try:
            resp = await self._http.get(
                self._settings.elevation_url, params={"latitude": lat, "longitude": lon})
            resp.raise_for_status()
            return {"elevation_m": float(resp.json()["elevation"][0])}
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise ElevationUnavailableError(
                hint="Enter the elevation manually.") from exc

    async def elevation(self, lat: float, lon: float) -> ElevationResponse:
        """Return elevation and ISA density."""
        height = await self.elevation_m(lat, lon)
        return ElevationResponse(elevation_m=height, air_density_kg_m3=isa_density(height))


def get_geo_service(
    session: AsyncSession = Depends(get_session),
    http: httpx.AsyncClient = Depends(get_http_client),
    settings: Settings = Depends(get_settings),
) -> GeoService:
    """Provide the geo service for a request."""
    return GeoService(session, http, settings)
