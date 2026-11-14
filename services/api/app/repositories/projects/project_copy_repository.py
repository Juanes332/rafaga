"""Deep copy of a project's children for the duplicate action."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def copy_children(session: AsyncSession, source: UUID, target: UUID) -> None:
    """Copy wind, geometry, alternatives and facade elements; no jobs."""
    p = {"s": source, "t": target}
    await session.execute(text(
        "UPDATE wind_climates t SET source=s.source, period_years=s.period_years, "
        "rose=s.rose, cache_key=s.cache_key, fetched_at=s.fetched_at, "
        "manual_direction_deg=s.manual_direction_deg, manual_u10_ms=s.manual_u10_ms, "
        "terrain_category=s.terrain_category, z0_m=s.z0_m "
        "FROM wind_climates s WHERE s.project_id=:s AND t.project_id=:t"), p)
    await session.execute(text(
        "UPDATE geometries t SET buildings=s.buildings FROM geometries s "
        "WHERE s.project_id=:s AND t.project_id=:t"), p)
    await session.execute(text("DELETE FROM alternatives WHERE project_id=:t"), p)
    olds = (await session.execute(text(
        "SELECT id, name, is_base, position FROM alternatives WHERE project_id=:s"), p)
    ).mappings().all()
    for old in olds:
        new_id = (await session.execute(text(
            "INSERT INTO alternatives (project_id, name, is_base, position) "
            "VALUES (:t, :n, :b, :pos) RETURNING id"),
            {"t": target, "n": old["name"], "b": old["is_base"], "pos": old["position"]},
        )).scalar_one()
        await session.execute(text(
            "INSERT INTO facade_elements (alternative_id, building_id, edge_index, type, params) "
            "SELECT :n, building_id, edge_index, type, params FROM facade_elements "
            "WHERE alternative_id=:o"), {"n": new_id, "o": old["id"]})
