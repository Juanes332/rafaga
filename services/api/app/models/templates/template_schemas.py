"""Pydantic models of the templates domain."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.settings.settings_schemas import LawsonTable, Thresholds

LOCATION_KEYS = frozenset(
    {"lat", "lon", "latitude", "longitude", "elevation", "location"}
)


class TemplatePayload(BaseModel):
    """The only keys a template may carry (BR-18: never a location)."""

    model_config = ConfigDict(extra="forbid")

    terrain_category: str | None = None
    z0_m: float | None = Field(default=None, ge=0.0001, le=3.0)
    thresholds: Thresholds | None = None
    lawson: LawsonTable | None = None
    facade_defaults: dict[str, Any] | None = None


class TemplateCreateRequest(BaseModel):
    """Body of POST /templates; the payload is validated by the service."""

    name: str = Field(min_length=1, max_length=80)
    payload: dict[str, Any]


class TemplateResponse(BaseModel):
    """A stored template summary."""

    id: UUID
    name: str
    created_at: datetime | None = None


class ApplyTemplateRequest(BaseModel):
    """Body of POST /projects/{id}/apply-template."""

    template_id: UUID


class WindClimateResponse(BaseModel):
    """The WindClimate schema of openapi.yaml."""

    source: str
    rose: dict[str, Any] | None = None
    period_years: int | None = None
    manual_direction_deg: float | None = None
    manual_u10_ms: float | None = None
    terrain_category: str
    z0_m: float
    ustar_ms: float | None = None
    air_density_kg_m3: float | None = None
    fetched_at: datetime | None = None
    from_cache: bool = False
