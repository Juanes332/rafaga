"""Shares domain business logic."""

from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_session
from app.core.errors.auth_errors import UserNotFoundError
from app.models.shares.share_schemas import ShareResponse
from app.repositories.shares import share_repository as repo
from app.repositories.users.user_repository import find_user_by_id
from app.security.jwt.jwt_guard import CurrentUser
from app.services.projects.project_access_service import (
    ProjectAccessService,
    get_project_access_service,
)


class ShareService:
    """Let an owner grant and revoke read access."""

    def __init__(self, session: AsyncSession, access: ProjectAccessService) -> None:
        """Bind collaborators."""
        self._session = session
        self._access = access

    async def list(self, user: CurrentUser, project_id: UUID) -> list[ShareResponse]:
        """List who the project is shared with (owner only)."""
        await self._access.resolve(project_id, user, write=True)
        rows = await repo.list_shares(self._session, project_id)
        return [ShareResponse(**r) for r in rows]

    async def grant(self, user: CurrentUser, project_id: UUID, target: UUID) -> None:
        """Grant read access to another user, idempotently."""
        await self._access.resolve(project_id, user, write=True)
        found = await find_user_by_id(self._session, target)
        if found is None or target == user.id:
            raise UserNotFoundError()
        await repo.upsert_share(self._session, project_id, target)
        await self._session.commit()

    async def revoke(self, user: CurrentUser, project_id: UUID, target: UUID) -> None:
        """Revoke a user's access."""
        await self._access.resolve(project_id, user, write=True)
        await repo.delete_share(self._session, project_id, target)
        await self._session.commit()


def get_share_service(
    session: AsyncSession = Depends(get_session),
    access: ProjectAccessService = Depends(get_project_access_service),
) -> ShareService:
    """Provide the share service for a request."""
    return ShareService(session, access)
