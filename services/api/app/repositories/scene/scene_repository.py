"""Data access for everything a scene compilation reads."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

DEFAULT_VEGETATION_CD = 0.2


async def load_scene_inputs(
    session: AsyncSession, project_id: UUID, alt_id: UUID
) -> Mapping[str, Any]:
    """Return project, geometry, roughness, drag and elements for a scene."""
    head = (await session.execute(
        text("SELECT p.analysis_height_m, g.version, g.buildings, w.z0_m, "
             "(SELECT vegetation_cd FROM user_settings u WHERE u.user_id = p.owner_id) AS cd "
             "FROM projects p JOIN geometries g ON g.project_id = p.id "
             "JOIN wind_climates w ON w.project_id = p.id WHERE p.id = :p"),
        {"p": project_id},
    )).mappings().one()
    rows = (await session.execute(
        text("SELECT id, building_id, edge_index, type, params FROM facade_elements "
             "WHERE alternative_id = :a ORDER BY created_at, id"),
        {"a": alt_id},
    )).mappings().all()
    return {**head, "cd": head["cd"] if head["cd"] is not None else DEFAULT_VEGETATION_CD,
            "elements": [dict(r) for r in rows]}
