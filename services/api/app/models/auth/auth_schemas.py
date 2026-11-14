"""Pydantic models of the auth domain."""

from pydantic import BaseModel, Field

from app.models.users.user_schemas import Email, UserResponse


class SetupStatusResponse(BaseModel):
    """Whether first-run setup is still pending."""

    needs_setup: bool


class CredentialsRequest(BaseModel):
    """Body of POST /auth/setup."""

    email: Email
    password: str = Field(max_length=256)


class LoginRequest(BaseModel):
    """Body of POST /auth/login."""

    email: Email
    password: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    """A bearer token with its lifetime and owner."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
