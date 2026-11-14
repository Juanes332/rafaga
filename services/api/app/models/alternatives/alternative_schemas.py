"""Pydantic models of the alternatives domain."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ResultsSummary(BaseModel):
    """Digest of an alternative's latest study."""

    study_id: UUID
    kind: str
    status: str
    k_mean: float | None = None


class AlternativeResponse(BaseModel):
    """One alternative of a project."""

    id: UUID
    name: str
    is_base: bool
    position: int
    element_count: int = 0
    latest_results_summary: ResultsSummary | None = None


class AlternativeCreateRequest(BaseModel):
    """Body of POST /projects/{id}/alternatives."""

    name: str = Field(min_length=1, max_length=80)
    from_alternative_id: UUID | None = None


class AlternativePatchRequest(BaseModel):
    """Body of PATCH /alternatives/{id}."""

    name: str | None = Field(default=None, min_length=1, max_length=80)
    position: int | None = Field(default=None, ge=0)


def summary_from_row(row: Any) -> ResultsSummary | None:
    """Build the latest-results digest from a joined list row."""
    if row["study_id"] is None:
        return None
    return ResultsSummary(
        study_id=row["study_id"], kind=row["study_kind"],
        status=derive_study_status(row["statuses"] or []), k_mean=row["k_mean"],
    )


def derive_study_status(statuses: list[str]) -> str:
    """Derive a study status from its heavy jobs (job-contract 2.1)."""
    unique = set(statuses)
    if not unique or unique == {"queued"}:
        return "queued"
    if unique & {"running", "queued"}:
        return "running"
    if unique == {"completed"}:
        return "completed"
    if "completed" in unique:
        return "partial"
    return "cancelled" if unique == {"cancelled"} else "failed"
