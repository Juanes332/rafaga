"""Data access for geometries and their facade-element references."""

from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import dumps


async def get_geometry(session: AsyncSession, project_id: UUID) -> dict[str, Any]:
    """Return {version, buildings} of a project."""
    row = await session.execute(
        text("SELECT version, buildings FROM geometries WHERE project_id = :p"),
        {"p": project_id},
    )
    return dict(row.mappings().one())


async def replace_if_version(
    session: AsyncSession, project_id: UUID, expected: int, buildings: list[dict[str, Any]]
) -> int | None:
    """Atomically store buildings when the version matches; return the new one."""
    result = await session.execute(
        text(
            "UPDATE geometries SET version = version + 1, updated_at = now(), "
            "buildings = CAST(:b AS jsonb) WHERE project_id = :p AND version = :v "
            "RETURNING version"
        ),
        {"p": project_id, "v": expected, "b": dumps(buildings)},
    )
    return result.scalar_one_or_none()


async def count_non_base_alternatives(session: AsyncSession, project_id: UUID) -> int:
    """Return how many derived alternatives the project has."""
    result = await session.execute(
        text("SELECT count(*) FROM alternatives WHERE project_id = :p AND NOT is_base"),
        {"p": project_id},
    )
    return result.scalar_one()


async def element_refs(session: AsyncSession, project_id: UUID) -> list[tuple[UUID, UUID, int]]:
    """Return (id, building_id, edge_index) of every facade element."""
    result = await session.execute(
        text(
            "SELECT e.id, e.building_id, e.edge_index FROM facade_elements e "
            "JOIN alternatives a ON a.id = e.alternative_id WHERE a.project_id = :p"
        ),
        {"p": project_id},
    )
    return [(r[0], r[1], r[2]) for r in result.all()]
