"""Data access for studies, their jobs and the inputs needed to create them."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import dumps

Row = Mapping[str, Any]

JOB_SELECT = (
    "SELECT j.*, r.id AS result_id FROM jobs j LEFT JOIN results r ON r.job_id = j.id"
)


async def find_alternative(session: AsyncSession, alternative_id: UUID) -> Row | None:
    """Return the alternative row, whoever owns its project."""
    result = await session.execute(
        text("SELECT id, project_id, name, is_base FROM alternatives WHERE id = :a"),
        {"a": alternative_id})
    return result.mappings().first()


async def load_inputs(session: AsyncSession, project_id: UUID) -> Row:
    """Return project, wind and base-geometry data for a simulation."""
    result = await session.execute(
        text("SELECT p.id, p.lat, p.lon, p.air_density_kg_m3, p.analysis_height_m, p.name, "
             "w.source, w.rose, w.cache_key, w.manual_direction_deg, w.manual_u10_ms, "
             "w.z0_m, g.buildings FROM projects p "
             "JOIN wind_climates w ON w.project_id = p.id "
             "JOIN geometries g ON g.project_id = p.id WHERE p.id = :p"),
        {"p": project_id})
    return result.mappings().one()


async def latest_solver_node(session: AsyncSession) -> Row | None:
    """Return the freshest solver row with an online flag."""
    result = await session.execute(text(
        "SELECT *, heartbeat_at > now() - interval '30 seconds' AS online "
        "FROM solver_nodes ORDER BY heartbeat_at DESC LIMIT 1"))
    return result.mappings().first()


async def insert_study(session: AsyncSession, values: Mapping[str, Any]) -> None:
    """Insert a study row with a caller-chosen id."""
    await session.execute(
        text("INSERT INTO studies (id, project_id, alternative_id, owner_id, kind, "
             "request, dx_m, auto_coarsened, aggregate_template) VALUES (:id, :project_id, "
             ":alternative_id, :owner_id, :kind, CAST(:request AS jsonb), :dx_m, "
             ":auto_coarsened, CAST(:aggregate_template AS jsonb))"),
        {**values, "request": dumps(values["request"]),
         "aggregate_template": None if values["aggregate_template"] is None
         else dumps(values["aggregate_template"])})


async def insert_job(session: AsyncSession, values: Mapping[str, Any]) -> None:
    """Insert one queued heavy job with a caller-chosen id."""
    await session.execute(
        text("INSERT INTO jobs (id, study_id, project_id, owner_id, kind, lane, priority, "
             "direction_deg, payload, device_requested) VALUES (:id, :study_id, :project_id, "
             ":owner_id, :kind, 'heavy', 0, :direction_deg, CAST(:payload AS jsonb), :device)"),
        {**values, "payload": dumps(values["payload"])})


async def find_study(session: AsyncSession, study_id: UUID) -> Row | None:
    """Return a study row with its alternative name, whoever owns it."""
    result = await session.execute(
        text("SELECT s.*, a.name AS alternative_name FROM studies s "
             "JOIN alternatives a ON a.id = s.alternative_id WHERE s.id = :s"),
        {"s": study_id})
    return result.mappings().first()


async def list_studies(session: AsyncSession, project_id: UUID) -> list[Row]:
    """Return the project's studies, newest first."""
    result = await session.execute(
        text("SELECT s.*, a.name AS alternative_name FROM studies s "
             "JOIN alternatives a ON a.id = s.alternative_id "
             "WHERE s.project_id = :p ORDER BY s.created_at DESC, s.id"), {"p": project_id})
    return list(result.mappings().all())


async def heavy_jobs_of(session: AsyncSession, study_ids: list[UUID]) -> list[Row]:
    """Return the heavy jobs of the given studies with their result ids."""
    result = await session.execute(
        text(f"{JOB_SELECT} WHERE j.study_id = ANY(:ids) AND j.lane = 'heavy' "
             "ORDER BY j.created_at, j.direction_deg"), {"ids": study_ids})
    return list(result.mappings().all())


async def cancel_study_jobs(session: AsyncSession, study_id: UUID) -> None:
    """Cancel queued jobs now and flag running ones (job-contract section 4)."""
    p = {"s": study_id}
    await session.execute(text(
        "UPDATE jobs SET status='cancelled', finished_at=now() "
        "WHERE study_id=:s AND status='queued'"), p)
    await session.execute(text(
        "UPDATE jobs SET cancel_requested=true WHERE study_id=:s AND status='running'"), p)
