"""Pydantic models of the comparisons domain."""

from typing import Any

from pydantic import BaseModel

from app.models.comfort.comfort_schemas import ComfortResponse
from app.models.results.result_schemas import ZoneArea, ZoneAreasResponse


class ComparisonCheckResponse(BaseModel):
    """Body of GET /comparisons/check."""

    comparable: bool
    differences: list[dict[str, Any]] = []


class ComparisonThresholds(BaseModel):
    """Thresholds used by a comparison."""

    k_accel: float
    k_stagnation: float
    dk_reduction: float


class ComparisonAreasResponse(BaseModel):
    """Body of GET /comparisons/areas."""

    a: ZoneAreasResponse
    b: ZoneAreasResponse
    reduction: ZoneArea
    thresholds: ComparisonThresholds


class ComparisonComfortResponse(BaseModel):
    """Body of GET /comparisons/comfort."""

    a: ComfortResponse
    b: ComfortResponse
