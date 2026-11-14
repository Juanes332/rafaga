"""Data access for project shares."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def list_shares(session: AsyncSession, project_id: UUID) -> list[Mapping[str, Any]]:
    """Return the users a project is shared with."""
    result = await session.execute(
        text("SELECT s.user_id, u.email::text AS email, s.created_at FROM project_shares s "
             "JOIN users u ON u.id = s.user_id WHERE s.project_id = :p ORDER BY s.created_at"),
        {"p": project_id},
    )
    return list(result.mappings().all())


async def upsert_share(session: AsyncSession, project_id: UUID, user_id: UUID) -> None:
    """Grant access idempotently."""
    await session.execute(
        text("INSERT INTO project_shares (project_id, user_id) VALUES (:p, :u) "
             "ON CONFLICT DO NOTHING"),
        {"p": project_id, "u": user_id},
    )


async def delete_share(session: AsyncSession, project_id: UUID, user_id: UUID) -> None:
    """Revoke access; absent shares are ignored."""
    await session.execute(
        text("DELETE FROM project_shares WHERE project_id = :p AND user_id = :u"),
        {"p": project_id, "u": user_id},
    )
