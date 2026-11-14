"""Derive the wire view of studies and jobs from rows."""

from collections.abc import Mapping, Sequence
from typing import Any

from app.models.simulations.simulation_schemas import (
    JobError,
    JobResponse,
    StudyResponse,
    StudySummaryResponse,
)


def job_hint(details: Mapping[str, Any] | None) -> str | None:
    """Return a short hint derived from structured error details."""
    if details and "proposed_dx_m" in details:
        return f"Use a cell size of {details['proposed_dx_m']} m or coarser."
    return None


def job_to_response(row: Mapping[str, Any]) -> JobResponse:
    """Build the Job schema from a joined job row."""
    error = None
    if row["error_code"]:
        error = JobError(code=row["error_code"], message=row["error_message"] or "",
                         hint=job_hint(row["error_details"]))
    fields = ("id", "study_id", "kind", "lane", "direction_deg", "status", "progress",
              "phase", "eta_seconds", "device_used", "resumable", "cancel_requested",
              "result_id", "created_at", "started_at", "finished_at")
    return JobResponse(**{k: row[k] for k in fields}, error=error)


def derive_status(statuses: Sequence[str]) -> str:
    """Derive the study status from its job statuses (contract 2.1)."""
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


def sector_of(direction_deg: float) -> int:
    """Return the 22.5-degree sector index containing a direction."""
    return int(((direction_deg + 11.25) % 360) // 22.5)


def coverage_of(template: Mapping[str, Any] | None, directions: Sequence[float]) -> float | None:
    """Return simulated rose frequency over the non-calm share."""
    if not template:
        return None
    rose = template["rose"]
    sectors = rose["sectors"]
    done = {sector_of(d) for d in directions}
    freq = sum(sectors[i]["frequency"] for i in done)
    return min(1.0, freq / (1.0 - rose["calm_fraction"]))


def _progress(jobs: Sequence[Any]) -> float:
    """Return the mean progress of a study's jobs."""
    return sum(j.progress for j in jobs) / len(jobs) if jobs else 0.0


def study_to_response(study: Mapping[str, Any], job_rows: Sequence[Mapping[str, Any]]) -> StudyResponse:
    """Build the Study schema."""
    jobs = [job_to_response(r) for r in job_rows]
    request = study["request"]
    directions = [float(d) for d in request.get("directions_deg") or [
        r["direction_deg"] for r in job_rows if r["direction_deg"] is not None]]
    return StudyResponse(
        id=study["id"], project_id=study["project_id"], alternative_id=study["alternative_id"],
        alternative_name=study["alternative_name"], kind=study["kind"],
        directions_deg=directions, section=request.get("section"), dx_m=study["dx_m"],
        device=request.get("device", "auto"), status=derive_status([j.status for j in jobs]),
        progress=_progress(jobs), coverage=coverage_of(study["aggregate_template"], directions),
        jobs=jobs, created_at=study["created_at"],
    )


def study_to_summary(study: Mapping[str, Any], job_rows: Sequence[Mapping[str, Any]]) -> StudySummaryResponse:
    """Build one list row from a study and its jobs."""
    full = study_to_response(study, job_rows)
    return StudySummaryResponse(
        id=full.id, alternative_name=full.alternative_name, kind=full.kind,
        directions_deg=full.directions_deg, status=full.status, progress=full.progress,
        device=full.device, created_at=full.created_at,
    )
