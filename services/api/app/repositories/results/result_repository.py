"""Data access for results rows and the job data they point to."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

Row = Mapping[str, Any]


async def find_result(session: AsyncSession, result_id: UUID) -> Row | None:
    """Return the result row by id, whoever owns the project."""
    r = await session.execute(text("SELECT * FROM results WHERE id = :i"), {"i": result_id})
    return r.mappings().first()


async def find_job_scene(session: AsyncSession, job_id: UUID) -> dict[str, Any] | None:
    """Return the compiled scene snapshotted in the job payload."""
    r = await session.execute(
        text("SELECT payload->'scene' FROM jobs WHERE id = :j"), {"j": job_id})
    row = r.first()
    return row[0] if row else None


async def list_study_results(session: AsyncSession, study_id: UUID) -> list[Row]:
    """Return the study's results ordered by direction."""
    r = await session.execute(
        text("SELECT * FROM results WHERE study_id = :s ORDER BY direction_deg, created_at"),
        {"s": study_id})
    return list(r.mappings().all())
