"""Jobs domain business logic: read, cancel, retry."""

import uuid
from collections.abc import Mapping
from typing import Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_session
from app.core.errors.simulation_errors import (
    JobNotCancellableError,
    JobNotFoundError,
    JobNotRetryableError,
)
from app.models.simulations.simulation_schemas import JobResponse
from app.repositories.jobs import job_repository as repo
from app.security.jwt.jwt_guard import CurrentUser
from app.services.projects.project_access_service import (
    ProjectAccessService,
    get_project_access_service,
)
from app.services.simulations.study_view import job_to_response


class JobService:
    """Let callers inspect, cancel and retry jobs of their projects."""

    def __init__(self, session: AsyncSession, access: ProjectAccessService) -> None:
        """Bind collaborators."""
        self._s = session
        self._access = access

    async def _visible(self, user: CurrentUser, job_id: UUID, write: bool) -> Mapping[str, Any]:
        """Return the job when its project is visible, else the opaque 404."""
        job = await repo.find_job(self._s, job_id)
        pid = job["project_id"] if job else uuid.UUID(int=0)
        await self._access.resolve(pid, user, write=write, not_found=JobNotFoundError)
        return job

    async def get(self, user: CurrentUser, job_id: UUID) -> JobResponse:
        """Return one job of any lane."""
        return job_to_response(await self._visible(user, job_id, False))

    async def cancel(self, user: CurrentUser, job_id: UUID) -> JobResponse:
        """Cancel a queued job now, or flag a running one."""
        await self._visible(user, job_id, True)
        changed = await repo.cancel_queued(self._s, job_id) or await repo.request_cancel(
            self._s, job_id)
        if not changed:
            raise JobNotCancellableError()
        await self._s.commit()
        return job_to_response(await repo.find_job(self._s, job_id))

    async def retry(self, user: CurrentUser, job_id: UUID) -> JobResponse:
        """Re-queue a failed resumable job."""
        await self._visible(user, job_id, True)
        if not await repo.requeue_failed(self._s, job_id):
            raise JobNotRetryableError()
        await self._s.commit()
        return job_to_response(await repo.find_job(self._s, job_id))


def get_job_service(
    session: AsyncSession = Depends(get_session),
    access: ProjectAccessService = Depends(get_project_access_service),
) -> JobService:
    """Provide the job service for a request."""
    return JobService(session, access)
