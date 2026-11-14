"""Projects domain business logic."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.config import Settings, get_settings
from app.core.database.database import get_session
from app.models.projects.project_schemas import (
    ProjectPatchRequest,
    ProjectResponse,
    ProjectSummaryResponse,
)
from app.repositories.projects import project_copy_repository as copies
from app.repositories.projects import project_repository as repo
from app.security.jwt.jwt_guard import CurrentUser
from app.services.projects.project_access_service import (
    ProjectAccessService,
    get_project_access_service,
)
from app.services.projects.project_files import remove_project_dirs


def to_response(row: Mapping[str, Any], role: str) -> ProjectResponse:
    """Build the Project schema from a row."""
    data = {k: v for k, v in row.items() if k not in ("owner_id", "role_on_project")}
    return ProjectResponse(**data, role_on_project=role)


class ProjectService:
    """Create, read, update, duplicate and delete projects."""

    def __init__(
        self, session: AsyncSession, access: ProjectAccessService, settings: Settings
    ) -> None:
        """Bind collaborators."""
        self._session = session
        self._access = access
        self._settings = settings

    async def list_for(self, user: CurrentUser) -> list[ProjectSummaryResponse]:
        """List owned and shared projects."""
        rows = await repo.list_projects(self._session, user.id)
        return [
            ProjectSummaryResponse(
                id=r["id"], name=r["name"], updated_at=r["updated_at"],
                has_location=r["lat"] is not None and r["lon"] is not None,
                role_on_project=r["role_on_project"],
            )
            for r in rows
        ]

    async def create(self, user: CurrentUser, name: str) -> ProjectResponse:
        """Create a project with its base alternative and empty geometry."""
        row = await repo.insert_project(self._session, user.id, name)
        await self._session.commit()
        return to_response(row, "owner")

    async def get(self, user: CurrentUser, project_id: UUID) -> ProjectResponse:
        """Return a project the caller owns or shares."""
        access = await self._access.resolve(project_id, user)
        row = await repo.find_project(self._session, project_id)
        return to_response(row, access.role_on_project)

    async def patch(
        self, user: CurrentUser, project_id: UUID, body: ProjectPatchRequest
    ) -> ProjectResponse:
        """Rename or change the analysis height."""
        await self._access.resolve(project_id, user, write=True)
        row = await repo.update_project(
            self._session, project_id, body.model_dump(exclude_none=True)
        )
        await self._session.commit()
        return to_response(row, "owner")

    async def delete(self, user: CurrentUser, project_id: UUID) -> None:
        """Delete a project, its jobs' queue entries and its files."""
        await self._access.resolve(project_id, user, write=True)
        await self.purge(project_id)

    async def purge(self, project_id: UUID) -> None:
        """Cancel active jobs, drop the rows and remove the directories."""
        await repo.cancel_active_jobs(self._session, project_id)
        await repo.delete_project(self._session, project_id)
        await self._session.commit()
        remove_project_dirs(self._settings, project_id)

    async def purge_owner(self, owner_id: UUID) -> None:
        """Purge every project an owner holds (before deleting the user)."""
        for pid in await repo.project_ids_of_owner(self._session, owner_id):
            await self.purge(pid)

    async def duplicate(self, user: CurrentUser, project_id: UUID) -> ProjectResponse:
        """Copy a project's setup without jobs or results."""
        await self._access.resolve(project_id, user, write=True)
        source = await repo.find_project(self._session, project_id)
        row = await repo.insert_project(
            self._session, user.id, f"Copia de {source['name']}"[:120]
        )
        fields = {k: source[k] for k in (
            "lat", "lon", "elevation_m", "elevation_source",
            "air_density_kg_m3", "analysis_height_m")}
        row = await repo.update_project(self._session, row["id"], fields)
        await copies.copy_children(self._session, project_id, row["id"])
        await self._session.commit()
        return to_response(row, "owner")


def get_project_service(
    session: AsyncSession = Depends(get_session),
    access: ProjectAccessService = Depends(get_project_access_service),
    settings: Settings = Depends(get_settings),
) -> ProjectService:
    """Provide the project service for a request."""
    return ProjectService(session, access, settings)
