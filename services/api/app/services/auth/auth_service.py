"""Auth domain business logic: setup, login, token issue."""

from collections.abc import Mapping
from typing import Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.config import Settings, get_settings
from app.core.database.database import get_session
from app.core.errors.auth_errors import (
    InvalidCredentialsError,
    PasswordTooShortError,
    SetupAlreadyDoneError,
)
from app.models.auth.auth_schemas import TokenResponse
from app.models.users.user_schemas import UserResponse
from app.repositories.users import user_repository as users
from app.security.jwt.token_codec import issue_token
from app.security.password.password_hasher import hash_password, verify_password

MIN_PASSWORD_LENGTH = 10


def ensure_password_length(password: str) -> None:
    """Raise PasswordTooShortError below the minimum length."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordTooShortError()


class AuthService:
    """Create the first architect and authenticate local users."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        """Bind the unit of work and the settings."""
        self._session = session
        self._settings = settings

    def _token(self, row: Mapping[str, Any]) -> TokenResponse:
        """Build the token response for a user row."""
        token, ttl = issue_token(self._settings, str(row["id"]), row["role"])
        return TokenResponse(
            access_token=token, expires_in=ttl, user=UserResponse(**row)
        )

    async def needs_setup(self) -> bool:
        """Return True while the users table is empty."""
        return await users.count_users(self._session) == 0

    async def setup(self, email: str, password: str) -> TokenResponse:
        """Create the first architect, only while no user exists."""
        ensure_password_length(password)
        await users.lock_user_creation(self._session)
        if await users.count_users(self._session) > 0:
            raise SetupAlreadyDoneError()
        row = await users.insert_user(
            self._session, email, hash_password(password), "architect"
        )
        await self._session.commit()
        return self._token(row)

    async def login(self, email: str, password: str) -> TokenResponse:
        """Return a token for valid credentials, else one uniform 401."""
        row = await users.find_user_by_email(self._session, email)
        stored = row["password_hash"] if row else None
        if not verify_password(password, stored) or row is None:
            raise InvalidCredentialsError()
        return self._token(row)


def get_auth_service(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    """Provide the auth service for a request."""
    return AuthService(session, settings)
