"""Pydantic models of the exports domain."""

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ExportThresholds(BaseModel):
    """Optional thresholds overriding the caller's settings."""

    k_accel: float | None = Field(default=None, gt=0)
    k_stagnation: float | None = Field(default=None, gt=0)
    dk_reduction: float | None = Field(default=None, lt=0)


class ExportCreateRequest(BaseModel):
    """Body of POST /exports."""

    result_id: UUID
    layer: Literal["k", "zones", "speed", "delta_k", "lawson"]
    compare_result_id: UUID | None = None
    thresholds: ExportThresholds | None = None
    dpi: int = Field(default=300, ge=300, le=600)

    @model_validator(mode="after")
    def _delta_needs_comparison(self) -> "ExportCreateRequest":
        """Require compare_result_id for the delta_k layer."""
        if self.layer == "delta_k" and self.compare_result_id is None:
            raise ValueError("compare_result_id is required for delta_k")
        return self


class ExportAcceptedResponse(BaseModel):
    """Body of the 202 answer."""

    export_id: UUID


class JobErrorResponse(BaseModel):
    """Error of a failed job."""

    code: str
    message: str
    hint: str | None = None


class ExportResponse(BaseModel):
    """The Export schema of openapi.yaml."""

    id: UUID
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    progress: float
    error: JobErrorResponse | None
    file_ready: bool


class ReportCreateRequest(BaseModel):
    """Body of POST /projects/{id}/reports."""

    study_ids: list[UUID] = Field(min_length=1)
    baseline_study_id: UUID | None = None
    include_comfort: bool = True


class ReportAcceptedResponse(BaseModel):
    """Body of the 202 answer."""

    report_id: UUID


class ReportResponse(BaseModel):
    """The Report schema of openapi.yaml."""

    id: UUID
    version: int
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    progress: float = 0.0
    error: JobErrorResponse | None = None
    created_at: Any = None
