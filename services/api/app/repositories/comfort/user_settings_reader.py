"""Read-only access to a caller's user_settings row."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def read_user_settings(session: AsyncSession, user_id: UUID) -> Mapping[str, Any] | None:
    """Return the settings row, or None before the first GET /settings."""
    r = await session.execute(
        text("SELECT thresholds, lawson, turbulence_intensity_default, vegetation_cd, "
             "alternatives_limit FROM user_settings WHERE user_id = :u"), {"u": user_id})
    return r.mappings().first()
