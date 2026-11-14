"""Data access for health probes and the solver capability rows."""

from collections.abc import Mapping
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def ping(session: AsyncSession) -> None:
    """Run the cheapest query to prove the database answers."""
    await session.execute(text("SELECT 1"))


async def freshest_solver_node(session: AsyncSession) -> Mapping[str, Any] | None:
    """Return the most recent solver row with an online flag."""
    result = await session.execute(text(
        "SELECT *, heartbeat_at > now() - interval '30 seconds' AS online "
        "FROM solver_nodes ORDER BY heartbeat_at DESC LIMIT 1"))
    return result.mappings().first()
