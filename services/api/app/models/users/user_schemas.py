"""Pydantic models of the users domain."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, Field

Role = Literal["architect", "reviewer"]


def _normalize_email(value: str) -> str:
    """Trim and lower-case an email, requiring a single @ with text around it."""
    value = value.strip().lower()
    local, _, domain = value.partition("@")
    if not local or not domain or "@" in domain or " " in value:
        raise ValueError("invalid email")
    return value


Email = Annotated[str, Field(max_length=254), AfterValidator(_normalize_email)]


class UserResponse(BaseModel):
    """A user as exposed to clients; never carries the hash."""

    id: UUID
    email: str
    role: Role
    created_at: datetime | None = None


class UserCreateRequest(BaseModel):
    """Body of POST /users."""

    email: Email
    password: str = Field(max_length=256)
    role: Role
