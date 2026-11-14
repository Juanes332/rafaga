"""Pydantic models of the simulations and jobs domains."""

from datetime import datetime
from typing import Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

Kind = Literal["plan2d", "section2d", "volume3d"]
Device = Literal["auto", "cpu", "gpu"]
Point = list[float]


class SectionLine(BaseModel):
    """A section line p0 (windward) to p1 (leeward) in ENU metres."""

    p0: Point = Field(min_length=2, max_length=2)
    p1: Point = Field(min_length=2, max_length=2)


class EstimateRequest(BaseModel):
    """Body of POST /simulations/estimate."""

    alternative_id: UUID
    kind: Kind
    directions_deg: list[float] | None = Field(default=None, min_length=1, max_length=16)
    section: SectionLine | None = None
    dx_m: float = Field(ge=0.25, le=20)
    device: Device = "auto"

    @model_validator(mode="after")
    def _kind_inputs(self) -> Self:
        """Require a section for section2d and angles within 0-360."""
        if self.kind == "section2d" and self.section is None:
            raise ValueError("section2d needs a section line")
        if any(not 0 <= d <= 360 for d in self.directions_deg or []):
            raise ValueError("directions must lie within 0-360")
        return self


class SimulationCreateRequest(EstimateRequest):
    """Body of POST /simulations."""

    auto_coarsen: bool = False


class EstimateResponse(BaseModel):
    """The Estimate schema."""

    device: Literal["cpu", "gpu"]
    nodes: int
    memory_bytes: int
    budget_bytes: int
    fits: bool
    proposed_dx_m: float | None
    rejected_reason: str | None
    eta_seconds: int
    grid: dict[str, Any]


class JobError(BaseModel):
    """Structured job failure."""

    code: str
    message: str
    hint: str | None = None


class JobResponse(BaseModel):
    """The Job schema."""

    id: UUID
    study_id: UUID | None = None
    kind: str
    lane: str
    direction_deg: float | None = None
    status: str
    progress: float
    phase: str | None = None
    eta_seconds: int | None = None
    device_used: str | None = None
    resumable: bool
    cancel_requested: bool = False
    error: JobError | None = None
    result_id: UUID | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class StudyResponse(BaseModel):
    """The Study schema."""

    id: UUID
    project_id: UUID
    alternative_id: UUID
    alternative_name: str
    kind: Kind
    directions_deg: list[float]
    section: SectionLine | None = None
    dx_m: float
    device: Device
    status: str
    progress: float
    coverage: float | None = None
    jobs: list[JobResponse]
    created_at: datetime


class StudySummaryResponse(BaseModel):
    """One row of GET /projects/{id}/simulations."""

    id: UUID
    alternative_name: str
    kind: str
    directions_deg: list[float]
    status: str
    progress: float
    device: str
    created_at: datetime
