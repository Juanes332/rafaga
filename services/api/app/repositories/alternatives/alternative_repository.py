"""Data access for alternatives."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

Row = Mapping[str, Any]

_LIST_SQL = """
SELECT a.id, a.name, a.is_base, a.position,
  (SELECT count(*) FROM facade_elements e WHERE e.alternative_id = a.id) AS element_count,
  ls.id AS study_id, ls.kind AS study_kind, ls.statuses, ls.k_mean
FROM alternatives a
LEFT JOIN LATERAL (
  SELECT s.id, s.kind,
    (SELECT array_agg(j.status) FROM jobs j
       WHERE j.study_id = s.id AND j.lane = 'heavy') AS statuses,
    (SELECT avg((r.stats->>'k_mean')::float) FROM results r
       WHERE r.study_id = s.id) AS k_mean
  FROM studies s WHERE s.alternative_id = a.id
  ORDER BY s.created_at DESC LIMIT 1) ls ON true
WHERE a.project_id = :p
ORDER BY a.is_base DESC, a.position, a.created_at
"""


async def find_alternative(session: AsyncSession, alt_id: UUID) -> Row | None:
    """Return the alternative row by id, whoever owns it."""
    result = await session.execute(
        text("SELECT id, project_id, name, is_base, position FROM alternatives WHERE id = :i"),
        {"i": alt_id},
    )
    return result.mappings().first()


async def list_alternatives(session: AsyncSession, project_id: UUID) -> list[Row]:
    """Return alternatives, base first, with counts and latest study."""
    result = await session.execute(text(_LIST_SQL), {"p": project_id})
    return list(result.mappings().all())


async def count_derived(session: AsyncSession, project_id: UUID) -> int:
    """Return how many non-base alternatives a project holds."""
    result = await session.execute(
        text("SELECT count(*) FROM alternatives WHERE project_id = :p AND NOT is_base"),
        {"p": project_id},
    )
    return result.scalar_one()


async def alternatives_limit_for(session: AsyncSession, user_id: UUID) -> int | None:
    """Return the user's stored alternatives limit, if a settings row exists."""
    result = await session.execute(
        text("SELECT alternatives_limit FROM user_settings WHERE user_id = :u"), {"u": user_id}
    )
    return result.scalar_one_or_none()


async def insert_alternative(session: AsyncSession, project_id: UUID, name: str) -> Row:
    """Insert a derived alternative at the end of the order."""
    result = await session.execute(
        text("INSERT INTO alternatives (project_id, name, position) VALUES (:p, :n, "
             "(SELECT coalesce(max(position), 0) + 1 FROM alternatives WHERE project_id = :p)) "
             "RETURNING id, project_id, name, is_base, position"),
        {"p": project_id, "n": name},
    )
    return result.mappings().one()


async def copy_elements(session: AsyncSession, source: UUID, target: UUID) -> None:
    """Copy every facade element from one alternative to another."""
    await session.execute(
        text("INSERT INTO facade_elements (alternative_id, building_id, edge_index, type, params) "
             "SELECT :t, building_id, edge_index, type, params FROM facade_elements "
             "WHERE alternative_id = :s ORDER BY created_at"),
        {"s": source, "t": target},
    )


async def rename_alternative(session: AsyncSession, alt_id: UUID, name: str) -> None:
    """Change an alternative's name."""
    await session.execute(text("UPDATE alternatives SET name = :n WHERE id = :i"), {"n": name, "i": alt_id})


async def derived_ids_in_order(session: AsyncSession, project_id: UUID) -> list[UUID]:
    """Return the non-base alternative ids in display order."""
    result = await session.execute(
        text("SELECT id FROM alternatives WHERE project_id = :p AND NOT is_base "
             "ORDER BY position, created_at"),
        {"p": project_id},
    )
    return [r[0] for r in result.all()]


async def set_positions(session: AsyncSession, ordered: list[UUID]) -> None:
    """Number the given derived alternatives 1..n in order."""
    for position, alt_id in enumerate(ordered, start=1):
        await session.execute(
            text("UPDATE alternatives SET position = :n WHERE id = :i"), {"n": position, "i": alt_id}
        )


async def delete_alternative(session: AsyncSession, alt_id: UUID) -> None:
    """Delete an alternative; elements and results cascade."""
    await session.execute(text("DELETE FROM alternatives WHERE id = :i"), {"i": alt_id})
