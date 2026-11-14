"""Data access for exports and the render jobs behind them."""

import json
from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

Row = Mapping[str, Any]


async def insert_export(session: AsyncSession, *, export_id: UUID, owner_id: UUID,
                        project_id: UUID, job_id: UUID, layer: str, params: dict[str, Any]) -> None:
    """Insert the export row linking owner, job and layer."""
    await session.execute(
        text("INSERT INTO exports (id, owner_id, project_id, job_id, layer, params) "
             "VALUES (:i, :o, :p, :j, :l, CAST(:pa AS jsonb))"),
        {"i": export_id, "o": owner_id, "p": project_id, "j": job_id, "l": layer,
         "pa": json.dumps(params)})


async def find_export(session: AsyncSession, export_id: UUID) -> Row | None:
    """Return the export joined with its job state."""
    r = await session.execute(
        text("SELECT e.*, j.status, j.progress, j.error_code, j.error_message "
             "FROM exports e JOIN jobs j ON j.id = e.job_id WHERE e.id = :i"), {"i": export_id})
    return r.mappings().first()


async def alternative_name(session: AsyncSession, alternative_id: UUID) -> str:
    """Return the name of an alternative."""
    r = await session.execute(
        text("SELECT name FROM alternatives WHERE id = :a"), {"a": alternative_id})
    return r.scalar_one()
