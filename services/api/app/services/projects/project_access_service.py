"""Resolve a caller's access to a project for every child domain."""

from collections.abc import Callable
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_session
from app.core.errors.error_contract import AppError
from app.core.errors.project_errors import ProjectNotFoundError
from app.repositories.projects import project_repository as repo
from app.security.jwt.jwt_guard import CurrentUser
from app.security.ownership.project_ownership_guard import (
    ProjectAccess,
    require_project_access,
)


class ProjectAccessService:
    """Load a project and let the ownership guard decide."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the unit of work."""
        self._session = session

    async def resolve(
        self,
        project_id: UUID,
        user: CurrentUser,
        *,
        write: bool = False,
        not_found: Callable[[], AppError] = ProjectNotFoundError,
    ) -> ProjectAccess:
        """Return access to the project or raise the not-found error."""
        project = await repo.find_project(self._session, project_id)
        shared = bool(project) and await repo.has_share(self._session, project_id, user.id)
        return require_project_access(project, shared, user, write=write, not_found=not_found)


def get_project_access_service(
    session: AsyncSession = Depends(get_session),
) -> ProjectAccessService:
    """Provide the access service for a request."""
    return ProjectAccessService(session)
