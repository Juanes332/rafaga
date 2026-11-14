"""Pydantic models of the results domain."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ResultResponse(BaseModel):
    """The Result schema of openapi.yaml."""

    id: UUID
    job_id: UUID
    study_id: UUID
    kind: str
    direction_deg: float | None
    device: str
    dx_m: float
    output_grid: dict[str, Any]
    stats: dict[str, Any]
    convergence: dict[str, Any]
    fields: list[str]
    images: list[str]
    comparability_key: str
    warnings: list[str]
    created_at: datetime | None = None


class ZoneArea(BaseModel):
    """Area of one zone."""

    zone: str
    area_m2: float
    percent: float


class ZoneThresholds(BaseModel):
    """Thresholds used for the zones."""

    k_accel: float
    k_stagnation: float


class ZoneAreasResponse(BaseModel):
    """The ZoneAreas schema of openapi.yaml."""

    result_id: UUID
    thresholds: ZoneThresholds
    fluid_area_m2: float
    zones: list[ZoneArea]


class Viewer3DResponse(BaseModel):
    """The Viewer3D schema of openapi.yaml."""

    scene: dict[str, Any] | None
    slices: list[dict[str, Any]]
    streamlines: list[Any]
