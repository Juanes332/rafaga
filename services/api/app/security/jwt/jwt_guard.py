"""Resolve the calling user from a bearer token."""

from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.config import Settings, get_settings
from app.core.database.database import get_session
from app.repositories.users.user_repository import find_user_by_id
from app.security.jwt.token_codec import decode_token

_bearer = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    """The authenticated caller, as the database knows them."""

    id: UUID
    email: str
    role: str


def _unauthorized(detail: str) -> HTTPException:
    """Build the single 401 every credential failure shares."""
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"}
    )


async def require_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
) -> CurrentUser:
    """Return the caller, or reject the request with 401.

    The user is re-read from the database so a deleted account stops
    working at once and the role is never taken from the token.
    """
    if credentials is None:
        raise _unauthorized("Missing bearer token")
    try:
        claims = decode_token(settings, credentials.credentials)
        user_id = UUID(str(claims["sub"]))
    except (jwt.PyJWTError, ValueError) as exc:
        raise _unauthorized("Invalid or expired token") from exc
    row = await find_user_by_id(session, user_id)
    if row is None:
        raise _unauthorized("Invalid or expired token")
    request.state.principal = f"user:{user_id}"
    return CurrentUser(id=row["id"], email=row["email"], role=row["role"])
