"""Data access for single-job reads and state transitions."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.simulations.study_repository import JOB_SELECT

Row = Mapping[str, Any]


async def find_job(session: AsyncSession, job_id: UUID) -> Row | None:
    """Return a job row (any lane) with its result id."""
    result = await session.execute(text(f"{JOB_SELECT} WHERE j.id = :j"), {"j": job_id})
    return result.mappings().first()


async def cancel_queued(session: AsyncSession, job_id: UUID) -> bool:
    """Cancel a queued job; return whether one changed."""
    result = await session.execute(text(
        "UPDATE jobs SET status='cancelled', finished_at=now() "
        "WHERE id=:j AND status='queued'"), {"j": job_id})
    return result.rowcount > 0


async def request_cancel(session: AsyncSession, job_id: UUID) -> bool:
    """Flag a running job for cooperative cancellation."""
    result = await session.execute(text(
        "UPDATE jobs SET cancel_requested=true WHERE id=:j AND status='running'"),
        {"j": job_id})
    return result.rowcount > 0


async def requeue_failed(session: AsyncSession, job_id: UUID) -> bool:
    """Re-queue a failed resumable job (job-contract section 4)."""
    result = await session.execute(text(
        "UPDATE jobs SET status='queued', resumable=false, error_code=NULL, "
        "error_message=NULL, error_details=NULL, progress=0, phase=NULL, "
        "cancel_requested=false, worker_id=NULL, finished_at=NULL "
        "WHERE id=:j AND status='failed' AND resumable"), {"j": job_id})
    return result.rowcount > 0
