"""Data access for wind_climates."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import dumps

Row = Mapping[str, Any]


async def find_wind(session: AsyncSession, project_id: UUID) -> Row:
    """Return the project's wind_climates row."""
    result = await session.execute(
        text("SELECT * FROM wind_climates WHERE project_id = :p"), {"p": project_id}
    )
    return result.mappings().one()


async def update_wind(session: AsyncSession, project_id: UUID, fields: dict[str, Any]) -> Row:
    """Update whitelisted columns; ``rose`` is serialized to jsonb."""
    allowed = {"source", "period_years", "rose", "cache_key", "fetched_at",
               "manual_direction_deg", "manual_u10_ms", "terrain_category", "z0_m"}
    cols = [c for c in fields if c in allowed]
    sets = ", ".join(
        f"{c} = CAST(:{c} AS jsonb)" if c == "rose" else f"{c} = :{c}" for c in cols
    )
    params = {c: (dumps(fields[c]) if c == "rose" else fields[c]) for c in cols}
    result = await session.execute(
        text(f"UPDATE wind_climates SET {sets + ', ' if sets else ''}updated_at = now() "
             "WHERE project_id = :p RETURNING *"),
        {"p": project_id, **params},
    )
    return result.mappings().one()
