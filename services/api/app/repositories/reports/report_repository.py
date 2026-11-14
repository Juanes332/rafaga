"""Data access for reports, the study snapshot and the render jobs."""

import json
from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

Row = Mapping[str, Any]
_JOINED = ("SELECT r.*, j.status, j.progress, j.error_code, j.error_message "
           "FROM reports r JOIN jobs j ON j.id = r.job_id ")


async def next_version(session: AsyncSession, project_id: UUID) -> int:
    """Return max(version)+1 for the project, serialised by a lock."""
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:p))"), {"p": str(project_id)})
    r = await session.execute(
        text("SELECT coalesce(max(version), 0) + 1 FROM reports WHERE project_id = :p"),
        {"p": project_id})
    return r.scalar_one()


async def insert_report(session: AsyncSession, *, report_id: UUID, project_id: UUID,
                        owner_id: UUID, job_id: UUID, version: int, params: dict[str, Any]) -> None:
    """Insert the report row."""
    await session.execute(
        text("INSERT INTO reports (id, project_id, owner_id, job_id, version, params) "
             "VALUES (:i, :p, :o, :j, :v, CAST(:pa AS jsonb))"),
        {"i": report_id, "p": project_id, "o": owner_id, "j": job_id, "v": version,
         "pa": json.dumps(params)})


async def find_report(session: AsyncSession, report_id: UUID) -> Row | None:
    """Return the report joined with its job state."""
    r = await session.execute(text(_JOINED + "WHERE r.id = :i"), {"i": report_id})
    return r.mappings().first()


async def list_reports(session: AsyncSession, project_id: UUID) -> list[Row]:
    """Return a project's reports, newest first."""
    r = await session.execute(
        text(_JOINED + "WHERE r.project_id = :p ORDER BY r.version DESC"), {"p": project_id})
    return list(r.mappings().all())


async def study_alternative_name(session: AsyncSession, study_id: UUID) -> str:
    """Return the alternative name behind a study."""
    r = await session.execute(
        text("SELECT a.name FROM studies s JOIN alternatives a ON a.id = s.alternative_id "
             "WHERE s.id = :s"), {"s": study_id})
    return r.scalar_one()


async def wind_row(session: AsyncSession, project_id: UUID) -> Row:
    """Return the project's wind climate row."""
    r = await session.execute(
        text("SELECT * FROM wind_climates WHERE project_id = :p"), {"p": project_id})
    return r.mappings().one()
