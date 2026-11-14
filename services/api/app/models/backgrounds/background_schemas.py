"""Pydantic models of the backgrounds domain."""

from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

Point2 = Annotated[list[float], Field(min_length=2, max_length=2)]


class Calibration(BaseModel):
    """Two image points and the real distance between them."""

    p1: Point2
    p2: Point2
    distance_m: float = Field(gt=0)


class Transform(BaseModel):
    """Placement of the plan relative to the project origin."""

    offset: Point2 = [0.0, 0.0]
    rotation_deg: float = 0.0
    scale: float = 1.0


class BackgroundResponse(BaseModel):
    """The BackgroundPlan schema of openapi.yaml."""

    id: UUID
    page_count: int
    page: int
    calibration: Calibration | None = None
    metres_per_pixel: float | None = None
    transform: Transform
    opacity: float


class BackgroundPatchRequest(BaseModel):
    """Body of PATCH /backgrounds/{id}."""

    page: int | None = Field(default=None, ge=1)
    calibration: Calibration | None = None
    transform: Transform | None = None
    opacity: float | None = Field(default=None, ge=0, le=1)
