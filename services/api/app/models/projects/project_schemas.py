"""Pydantic models of the projects domain."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    """Body of POST /projects."""

    name: str = Field(min_length=1, max_length=120)


class ProjectPatchRequest(BaseModel):
    """Body of PATCH /projects/{id}."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    analysis_height_m: float | None = Field(default=None, ge=0.5, le=3.0)


class ProjectResponse(BaseModel):
    """The full Project schema of openapi.yaml."""

    id: UUID
    name: str
    lat: float | None
    lon: float | None
    elevation_m: float | None = None
    elevation_source: Literal["open_meteo", "manual"] | None = None
    air_density_kg_m3: float | None = None
    analysis_height_m: float
    role_on_project: Literal["owner", "reviewer"]
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProjectSummaryResponse(BaseModel):
    """One row of GET /projects."""

    id: UUID
    name: str
    has_location: bool
    updated_at: datetime
    role_on_project: Literal["owner", "reviewer"]
