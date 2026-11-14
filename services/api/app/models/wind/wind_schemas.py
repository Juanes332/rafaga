"""Pydantic models of the wind domain."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Terrain = Literal["open_sea", "open", "suburban", "urban", "dense_urban"]


class WindPatchRequest(BaseModel):
    """Body of PATCH /projects/{id}/wind."""

    source: Literal["era5", "manual"] | None = None
    manual_direction_deg: float | None = Field(default=None, ge=0, le=360)
    manual_u10_ms: float | None = Field(default=None, ge=0.5, le=60)
    terrain_category: Terrain | None = None
    z0_m: float | None = Field(default=None, ge=0.0001, le=3.0)


class Era5Request(BaseModel):
    """Body of POST /projects/{id}/wind/era5."""

    years: int = Field(default=10, ge=1, le=40)


class WindClimateResponse(BaseModel):
    """The WindClimate schema of openapi.yaml."""

    source: Literal["era5", "manual"]
    rose: dict[str, Any] | None
    period_years: int
    manual_direction_deg: float | None
    manual_u10_ms: float | None
    terrain_category: Terrain
    z0_m: float
    ustar_ms: float | None = None
    air_density_kg_m3: float | None = None
    fetched_at: datetime | None = None
    from_cache: bool = False
