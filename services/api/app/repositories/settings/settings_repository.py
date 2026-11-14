"""Data access for user_settings."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import dumps

_COLS = ("thresholds, lawson, turbulence_intensity_default, vegetation_cd, "
         "alternatives_limit")


async def find_settings(session: AsyncSession, user_id: UUID) -> Mapping[str, Any] | None:
    """Return the stored settings row, or None."""
    result = await session.execute(
        text(f"SELECT {_COLS} FROM user_settings WHERE user_id = :u"), {"u": user_id}
    )
    return result.mappings().first()


async def upsert_settings(
    session: AsyncSession, user_id: UUID, data: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Insert or replace the settings row and return it."""
    result = await session.execute(
        text(
            "INSERT INTO user_settings (user_id, thresholds, lawson, "
            "turbulence_intensity_default, vegetation_cd, alternatives_limit) "
            "VALUES (:u, CAST(:t AS jsonb), CAST(:l AS jsonb), :ti, :cd, :al) "
            "ON CONFLICT (user_id) DO UPDATE SET thresholds = EXCLUDED.thresholds, "
            "lawson = EXCLUDED.lawson, "
            "turbulence_intensity_default = EXCLUDED.turbulence_intensity_default, "
            "vegetation_cd = EXCLUDED.vegetation_cd, "
            f"alternatives_limit = EXCLUDED.alternatives_limit RETURNING {_COLS}"
        ),
        {"u": user_id, "t": dumps(data["thresholds"]), "l": dumps(data["lawson"]),
         "ti": data["turbulence_intensity_default"], "cd": data["vegetation_cd"],
         "al": data["alternatives_limit"]},
    )
    return result.mappings().one()
