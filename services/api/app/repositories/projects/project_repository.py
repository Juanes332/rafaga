"""Data access for projects and their one-to-one children."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

Row = Mapping[str, Any]
_COLS = (
    "id, owner_id, name, lat, lon, elevation_m, elevation_source, "
    "air_density_kg_m3, analysis_height_m, created_at, updated_at"
)


async def insert_project(session: AsyncSession, owner_id: UUID, name: str) -> Row:
    """Insert a project with its base alternative, geometry and wind row."""
    row = (
        await session.execute(
            text(f"INSERT INTO projects (owner_id, name) VALUES (:o, :n) RETURNING {_COLS}"),
            {"o": owner_id, "n": name},
        )
    ).mappings().one()
    pid = {"p": row["id"]}
    await session.execute(
        text("INSERT INTO alternatives (project_id, name, is_base, position) "
             "VALUES (:p, 'Caso base', true, 0)"), pid)
    await session.execute(text("INSERT INTO geometries (project_id) VALUES (:p)"), pid)
    await session.execute(text("INSERT INTO wind_climates (project_id) VALUES (:p)"), pid)
    return row


async def find_project(session: AsyncSession, project_id: UUID) -> Row | None:
    """Return the project row by id, whoever owns it."""
    result = await session.execute(
        text(f"SELECT {_COLS} FROM projects WHERE id = :p"), {"p": project_id}
    )
    return result.mappings().first()


async def has_share(session: AsyncSession, project_id: UUID, user_id: UUID) -> bool:
    """Return whether the user holds a share on the project."""
    result = await session.execute(
        text("SELECT 1 FROM project_shares WHERE project_id = :p AND user_id = :u"),
        {"p": project_id, "u": user_id},
    )
    return result.first() is not None


async def list_projects(session: AsyncSession, user_id: UUID) -> list[Row]:
    """Return owned and shared projects, newest first."""
    result = await session.execute(
        text(
            f"SELECT {_COLS}, CASE WHEN owner_id = :u THEN 'owner' ELSE 'reviewer' "
            "END AS role_on_project FROM projects p WHERE owner_id = :u OR EXISTS "
            "(SELECT 1 FROM project_shares s WHERE s.project_id = p.id AND s.user_id = :u) "
            "ORDER BY updated_at DESC"
        ),
        {"u": user_id},
    )
    return list(result.mappings().all())


async def update_project(session: AsyncSession, project_id: UUID, fields: dict[str, Any]) -> Row:
    """Update whitelisted columns and bump updated_at."""
    allowed = {"name", "analysis_height_m", "lat", "lon", "elevation_m",
               "elevation_source", "air_density_kg_m3"}
    cols = [c for c in fields if c in allowed]
    sets = ", ".join(f"{c} = :{c}" for c in cols)
    sets = f"{sets}, " if sets else ""
    result = await session.execute(
        text(f"UPDATE projects SET {sets}updated_at = now() WHERE id = :p RETURNING {_COLS}"),
        {"p": project_id, **{c: fields[c] for c in cols}},
    )
    return result.mappings().one()


async def touch_project(session: AsyncSession, project_id: UUID) -> None:
    """Bump updated_at after a child resource changed."""
    await session.execute(
        text("UPDATE projects SET updated_at = now() WHERE id = :p"), {"p": project_id}
    )


async def cancel_active_jobs(session: AsyncSession, project_id: UUID) -> None:
    """Cancel queued jobs now and flag running ones for cancellation."""
    p = {"p": project_id}
    await session.execute(text(
        "UPDATE jobs SET status='cancelled', finished_at=now() "
        "WHERE project_id=:p AND status='queued'"), p)
    await session.execute(text(
        "UPDATE jobs SET cancel_requested=true "
        "WHERE project_id=:p AND status='running'"), p)


async def delete_project(session: AsyncSession, project_id: UUID) -> None:
    """Delete the project row; every child cascades."""
    await session.execute(text("DELETE FROM projects WHERE id = :p"), {"p": project_id})


async def project_ids_of_owner(session: AsyncSession, owner_id: UUID) -> list[UUID]:
    """Return the ids of every project an owner holds."""
    result = await session.execute(
        text("SELECT id FROM projects WHERE owner_id = :o"), {"o": owner_id}
    )
    return [r[0] for r in result.all()]
