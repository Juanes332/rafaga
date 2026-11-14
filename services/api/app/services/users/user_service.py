"""Users domain business logic."""

from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_session
from app.core.errors.auth_errors import (
    CannotDeleteSelfError,
    EmailTakenError,
    UserNotFoundError,
)
from app.models.users.user_schemas import UserCreateRequest, UserResponse
from app.repositories.users import user_repository as repo
from app.security.jwt.jwt_guard import CurrentUser
from app.security.password.password_hasher import hash_password
from app.services.auth.auth_service import ensure_password_length
from app.services.projects.project_service import ProjectService, get_project_service


class UserService:
    """Manage local accounts; architect-only, enforced at the router."""

    def __init__(self, session: AsyncSession, projects: ProjectService) -> None:
        """Bind the unit of work and the project service."""
        self._session = session
        self._projects = projects

    async def list_all(self) -> list[UserResponse]:
        """List every local user."""
        return [UserResponse(**r) for r in await repo.list_users(self._session)]

    async def create(self, body: UserCreateRequest) -> UserResponse:
        """Create a user, refusing short passwords and duplicate emails."""
        ensure_password_length(body.password)
        if await repo.find_user_by_email(self._session, body.email):
            raise EmailTakenError()
        row = await repo.insert_user(
            self._session, body.email, hash_password(body.password), body.role
        )
        await self._session.commit()
        return UserResponse(**row)

    async def delete(self, caller: CurrentUser, user_id: UUID) -> None:
        """Delete another user together with their projects and shares."""
        if user_id == caller.id:
            raise CannotDeleteSelfError()
        if await repo.find_user_by_id(self._session, user_id) is None:
            raise UserNotFoundError()
        await self._projects.purge_owner(user_id)
        await repo.delete_user(self._session, user_id)
        await self._session.commit()


def get_user_service(
    session: AsyncSession = Depends(get_session),
    projects: ProjectService = Depends(get_project_service),
) -> UserService:
    """Provide the user service for a request."""
    return UserService(session, projects)
