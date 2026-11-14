"""Data access for facade elements."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import dumps

Row = Mapping[str, Any]
_COLS = "e.id, e.alternative_id, e.building_id, e.edge_index, e.type, e.params"


async def find_element(session: AsyncSession, element_id: UUID) -> Row | None:
    """Return an element with its alternative's project and base flag."""
    result = await session.execute(
        text(f"SELECT {_COLS}, a.project_id, a.is_base FROM facade_elements e "
             "JOIN alternatives a ON a.id = e.alternative_id WHERE e.id = :i"),
        {"i": element_id},
    )
    return result.mappings().first()


async def list_elements(session: AsyncSession, alt_id: UUID) -> list[Row]:
    """Return an alternative's elements in creation order."""
    result = await session.execute(
        text(f"SELECT {_COLS} FROM facade_elements e WHERE e.alternative_id = :a "
             "ORDER BY e.created_at, e.id"),
        {"a": alt_id},
    )
    return list(result.mappings().all())


async def insert_element(
    session: AsyncSession, alt_id: UUID, building_id: UUID, edge_index: int, type_: str, params: dict[str, Any]
) -> Row:
    """Insert an element and return it."""
    result = await session.execute(
        text("INSERT INTO facade_elements (alternative_id, building_id, edge_index, type, params) "
             "VALUES (:a, :b, :e, :t, CAST(:p AS jsonb)) "
             "RETURNING id, alternative_id, building_id, edge_index, type, params"),
        {"a": alt_id, "b": building_id, "e": edge_index, "t": type_, "p": dumps(params)},
    )
    return result.mappings().one()


async def update_params(session: AsyncSession, element_id: UUID, params: dict[str, Any]) -> None:
    """Replace an element's params."""
    await session.execute(
        text("UPDATE facade_elements SET params = CAST(:p AS jsonb) WHERE id = :i"),
        {"p": dumps(params), "i": element_id},
    )


async def delete_element(session: AsyncSession, element_id: UUID) -> None:
    """Delete one element."""
    await session.execute(text("DELETE FROM facade_elements WHERE id = :i"), {"i": element_id})


async def project_buildings(session: AsyncSession, project_id: UUID) -> list[dict[str, Any]]:
    """Return the project's base buildings."""
    result = await session.execute(
        text("SELECT buildings FROM geometries WHERE project_id = :p"), {"p": project_id}
    )
    return result.scalar_one_or_none() or []


async def has_derived(session: AsyncSession, project_id: UUID) -> bool:
    """Return whether the project holds any non-base alternative."""
    result = await session.execute(
        text("SELECT EXISTS (SELECT 1 FROM alternatives WHERE project_id = :p AND NOT is_base)"),
        {"p": project_id},
    )
    return result.scalar_one()
