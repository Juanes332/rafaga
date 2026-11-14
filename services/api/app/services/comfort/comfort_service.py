"""Comfort domain business logic."""

from typing import Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_session
from app.core.errors.result_errors import RoseMissingError, StudyNotFoundError
from app.models.comfort.comfort_schemas import ComfortResponse
from app.repositories.comfort import comfort_repository as repo
from app.repositories.results.result_repository import list_study_results
from app.security.jwt.jwt_guard import CurrentUser
from app.services.comfort.aggregate_payload import build_aggregate_payload
from app.services.comfort.lawson_service import caller_settings, lawson_hash
from app.services.projects.project_access_service import (
    ProjectAccessService,
    get_project_access_service,
)

_JOB_STATUS = {"queued": "pending", "running": "running", "failed": "failed",
               "cancelled": "failed", "completed": "failed"}


def _completed(study_id: UUID, digest: str, row: Any) -> ComfortResponse:
    """Map a comfort_results row to the response."""
    return ComfortResponse(
        study_id=study_id, status="completed", lawson_hash=digest, coverage=row["coverage"],
        partial=row["partial"], class_areas=row["class_areas"],
        safety_areas=[{**s, "class": s.get("label", s.get("class"))} for s in row["safety_areas"]],
        image=row["images"][0]["name"] if row["images"] else None,
        field=row["fields"][0]["name"] if row["fields"] else None)


class ComfortService:
    """Read and recompute Lawson comfort for a study."""

    def __init__(self, session: AsyncSession, access: ProjectAccessService) -> None:
        """Bind collaborators."""
        self._session, self._access = session, access

    async def study(self, user: CurrentUser, study_id: UUID, *, write: bool = False) -> dict:
        """Return the study row after the ownership check."""
        row = await repo.find_study(self._session, study_id)
        pid = row["project_id"] if row else UUID(int=0)
        await self._access.resolve(pid, user, write=write, not_found=StudyNotFoundError)
        return dict(row)

    async def _current(self, user: CurrentUser, study: dict) -> tuple[dict, dict, str]:
        """Return the template, the caller's settings and the current hash."""
        template = study["aggregate_template"]
        if not template:
            raise RoseMissingError()
        cfg = await caller_settings(self._session, user.id)
        digest = lawson_hash(cfg["lawson"], cfg["turbulence"], template["rose"].get("cache_key"))
        return template, cfg, digest

    async def _state(self, study_id: UUID, digest: str) -> ComfortResponse:
        """Return completed data, else the aggregate job's state."""
        row = await repo.find_comfort(self._session, study_id, digest)
        if row is not None:
            return _completed(study_id, digest, row)
        job = await repo.find_aggregate_job(self._session, study_id, digest)
        status = _JOB_STATUS[job["status"]] if job else "pending"
        return ComfortResponse(study_id=study_id, status=status, lawson_hash=digest)

    async def get(self, user: CurrentUser, study_id: UUID) -> ComfortResponse:
        """Return the comfort for the caller's current Lawson table."""
        study = await self.study(user, study_id)
        _, _, digest = await self._current(user, study)
        return await self._state(study_id, digest)

    async def recompute(self, user: CurrentUser, study_id: UUID) -> tuple[ComfortResponse, int]:
        """Enqueue the aggregate job unless one already covers this hash."""
        study = await self.study(user, study_id, write=True)
        template, cfg, digest = await self._current(user, study)
        current = await self._state(study_id, digest)
        if current.status == "completed":
            return current, 200
        if current.status in ("pending", "running") and await repo.find_aggregate_job(
                self._session, study_id, digest):
            return current, 202
        results = await list_study_results(self._session, study_id)
        payload = build_aggregate_payload(
            project_id=study["project_id"], study_id=study_id, template=template,
            results=[dict(r) for r in results], lawson=cfg["lawson"], turbulence=cfg["turbulence"])
        await repo.insert_light_job(self._session, project_id=study["project_id"],
                                    owner_id=user.id, study_id=study_id, kind="aggregate",
                                    payload=payload)
        await self._session.commit()
        return ComfortResponse(study_id=study_id, status="pending", lawson_hash=digest), 202


def get_comfort_service(
    session: AsyncSession = Depends(get_session),
    access: ProjectAccessService = Depends(get_project_access_service),
) -> ComfortService:
    """Provide the comfort service for a request."""
    return ComfortService(session, access)
