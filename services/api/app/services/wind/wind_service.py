"""Wind domain business logic."""

import math
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import httpx
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.config import Settings, get_settings
from app.core.database.database import get_session
from app.core.errors.geo_errors import LocationMissingError, RoseMissingError
from app.models.wind.wind_schemas import Era5Request, WindClimateResponse, WindPatchRequest
from app.repositories.geo import external_cache_repository as cache
from app.repositories.projects import project_repository as projects
from app.repositories.wind import wind_repository as repo
from app.security.jwt.jwt_guard import CurrentUser
from app.services.geo.external_http import get_http_client
from app.services.geo.geo_service import TERRAIN
from app.services.projects.project_access_service import (
    ProjectAccessService,
    get_project_access_service,
)
from app.services.wind.wind_era5_client import fetch_hourly_wind
from app.services.wind.wind_stats import build_rose

KAPPA = 0.41
ERA5_TTL_DAYS = 365
Z0_BY_CATEGORY = dict(TERRAIN)


def friction_velocity(u10: float, z0: float) -> float:
    """Return u* = kappa U10 / ln((10 + z0) / z0)."""
    return KAPPA * u10 / math.log((10.0 + z0) / z0)


def to_climate(
    row: Mapping[str, Any], density: float | None, from_cache: bool = False
) -> WindClimateResponse:
    """Build the WindClimate response from a row and project density."""
    u10 = row["manual_u10_ms"]
    return WindClimateResponse(
        source=row["source"], rose=row["rose"], period_years=row["period_years"],
        manual_direction_deg=row["manual_direction_deg"], manual_u10_ms=u10,
        terrain_category=row["terrain_category"], z0_m=row["z0_m"],
        ustar_ms=friction_velocity(u10, row["z0_m"]) if u10 else None,
        air_density_kg_m3=density, fetched_at=row["fetched_at"], from_cache=from_cache,
    )


class WindService:
    """Read, patch and fill the wind climate of a project."""

    def __init__(self, session: AsyncSession, access: ProjectAccessService,
                 http: httpx.AsyncClient, settings: Settings) -> None:
        """Bind collaborators."""
        self._session, self._access = session, access
        self._http, self._settings = http, settings

    async def get(self, user: CurrentUser, project_id: UUID) -> WindClimateResponse:
        """Return the stored climate."""
        await self._access.resolve(project_id, user)
        return await self._current(project_id)

    async def _current(self, project_id: UUID, from_cache: bool = False) -> WindClimateResponse:
        """Load row and project density into a response."""
        project = await projects.find_project(self._session, project_id)
        row = await repo.find_wind(self._session, project_id)
        return to_climate(row, project["air_density_kg_m3"], from_cache)

    async def patch(
        self, user: CurrentUser, project_id: UUID, body: WindPatchRequest
    ) -> WindClimateResponse:
        """Apply a partial update, resolving category to z0."""
        await self._access.resolve(project_id, user, write=True)
        fields = body.model_dump(exclude_none=True)
        if "terrain_category" in fields and "z0_m" not in fields:
            fields["z0_m"] = Z0_BY_CATEGORY[fields["terrain_category"]]
        if fields.get("source") == "era5":
            if (await repo.find_wind(self._session, project_id))["rose"] is None:
                raise RoseMissingError()
        await repo.update_wind(self._session, project_id, fields)
        await projects.touch_project(self._session, project_id)
        await self._session.commit()
        return await self._current(project_id)

    async def fetch_era5(
        self, user: CurrentUser, project_id: UUID, body: Era5Request
    ) -> WindClimateResponse:
        """Fill the rose from ERA5 (or the cache) and switch to era5."""
        await self._access.resolve(project_id, user, write=True)
        project = await projects.find_project(self._session, project_id)
        if project["lat"] is None or project["lon"] is None:
            raise LocationMissingError()
        key = f"{round(project['lat'], 1):.1f},{round(project['lon'], 1):.1f}:{body.years}"
        rose = await cache.get_cached(self._session, "era5", key)
        from_cache = rose is not None
        if rose is None:
            rose = await self._compute(project, body.years)
            await cache.put_cached(self._session, "era5", key, rose, ERA5_TTL_DAYS)
        await repo.update_wind(self._session, project_id, {
            "source": "era5", "rose": rose, "cache_key": key, "period_years": body.years,
            "fetched_at": datetime.now(UTC)})
        await self._session.commit()
        return await self._current(project_id, from_cache)

    async def _compute(self, project: Mapping[str, Any], years: int) -> dict:
        """Download hourly wind and build the rose."""
        speed, direction = await fetch_hourly_wind(
            self._http, self._settings, project["lat"], project["lon"], years)
        return build_rose(speed, direction, years)


def get_wind_service(
    session: AsyncSession = Depends(get_session),
    access: ProjectAccessService = Depends(get_project_access_service),
    http: httpx.AsyncClient = Depends(get_http_client),
    settings: Settings = Depends(get_settings),
) -> WindService:
    """Provide the wind service for a request."""
    return WindService(session, access, http, settings)
