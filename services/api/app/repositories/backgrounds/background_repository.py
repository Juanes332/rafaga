"""Data access for background plans joined with their upload."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import dumps

Row = Mapping[str, Any]
_SELECT = (
    "SELECT b.id, b.project_id, b.upload_id, b.page_count, b.page, b.calibration, "
    "b.transform, b.opacity, u.path, u.filename FROM background_plans b "
    "JOIN uploads u ON u.id = b.upload_id"
)


async def insert_plan(
    session: AsyncSession, project_id: UUID, upload_id: UUID, page_count: int
) -> UUID:
    """Create the plan row for an uploaded background."""
    result = await session.execute(
        text("INSERT INTO background_plans (project_id, upload_id, page_count) "
             "VALUES (:p, :u, :c) RETURNING id"),
        {"p": project_id, "u": upload_id, "c": page_count},
    )
    return result.scalar_one()


async def get_plan(session: AsyncSession, plan_id: UUID) -> Row | None:
    """Return a plan by id, whoever owns the project."""
    result = await session.execute(text(f"{_SELECT} WHERE b.id = :i"), {"i": plan_id})
    return result.mappings().first()


async def list_plans(session: AsyncSession, project_id: UUID) -> list[Row]:
    """Return the plans of a project, oldest first."""
    result = await session.execute(
        text(f"{_SELECT} WHERE b.project_id = :p ORDER BY u.created_at"), {"p": project_id}
    )
    return list(result.mappings().all())


async def update_plan(session: AsyncSession, plan_id: UUID, fields: dict[str, Any]) -> None:
    """Update page, calibration, transform and opacity."""
    sets, params = [], {"i": plan_id}
    for key, value in fields.items():
        if key in ("calibration", "transform"):
            sets.append(f"{key} = CAST(:{key} AS jsonb)")
            params[key] = dumps(value)
        else:
            sets.append(f"{key} = :{key}")
            params[key] = value
    if sets:
        await session.execute(
            text(f"UPDATE background_plans SET {', '.join(sets)} WHERE id = :i"), params
        )
