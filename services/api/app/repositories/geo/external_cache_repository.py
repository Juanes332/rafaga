"""Data access for the external_cache table."""

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import dumps


async def get_cached(session: AsyncSession, kind: str, key: str) -> Any | None:
    """Return the unexpired payload for a key, or None."""
    result = await session.execute(
        text("SELECT payload FROM external_cache WHERE kind=:k AND key=:key "
             "AND expires_at > now()"),
        {"k": kind, "key": key},
    )
    row = result.first()
    return None if row is None else row[0]


async def put_cached(
    session: AsyncSession, kind: str, key: str, payload: Any, ttl_days: int
) -> None:
    """Upsert a payload with a TTL in days."""
    await session.execute(
        text("INSERT INTO external_cache (kind, key, payload, expires_at) VALUES "
             "(:k, :key, CAST(:p AS jsonb), now() + make_interval(days => :d)) "
             "ON CONFLICT (kind, key) DO UPDATE SET payload = EXCLUDED.payload, "
             "fetched_at = now(), expires_at = EXCLUDED.expires_at"),
        {"k": kind, "key": key, "p": dumps(payload), "d": ttl_days},
    )
    await session.commit()
