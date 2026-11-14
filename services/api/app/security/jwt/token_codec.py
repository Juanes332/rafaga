"""Encode and decode the HS256 bearer tokens."""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.configs.config import Settings


def issue_token(settings: Settings, user_id: str, role: str) -> tuple[str, int]:
    """Return a signed token and its lifetime in seconds."""
    ttl = settings.jwt_ttl_minutes * 60
    now = datetime.now(UTC)
    claims = {"sub": user_id, "role": role, "iat": now, "exp": now + timedelta(seconds=ttl)}
    return jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm), ttl


def decode_token(settings: Settings, token: str) -> dict[str, Any]:
    """Return the verified claims, raising jwt.PyJWTError otherwise."""
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "sub"]},
    )
