"""Data access for templates."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import dumps


async def list_templates(session: AsyncSession, owner_id: UUID) -> list[Mapping[str, Any]]:
    """Return the owner's templates, newest first."""
    result = await session.execute(
        text("SELECT id, name, created_at FROM templates WHERE owner_id=:o "
             "ORDER BY created_at DESC"), {"o": owner_id})
    return list(result.mappings().all())


async def insert_template(
    session: AsyncSession, owner_id: UUID, name: str, payload: dict[str, Any]
) -> Mapping[str, Any]:
    """Insert a template and return its summary row."""
    result = await session.execute(
        text("INSERT INTO templates (owner_id, name, payload) "
             "VALUES (:o, :n, CAST(:p AS jsonb)) RETURNING id, name, created_at"),
        {"o": owner_id, "n": name, "p": dumps(payload)})
    return result.mappings().one()


async def find_template(session: AsyncSession, template_id: UUID) -> Mapping[str, Any] | None:
    """Return a template row by id, whoever owns it."""
    result = await session.execute(
        text("SELECT id, owner_id, name, payload FROM templates WHERE id=:i"),
        {"i": template_id})
    return result.mappings().first()


async def delete_template(session: AsyncSession, template_id: UUID) -> None:
    """Delete a template row."""
    await session.execute(text("DELETE FROM templates WHERE id=:i"), {"i": template_id})


async def apply_roughness(
    session: AsyncSession, project_id: UUID, terrain: str | None, z0: float | None
) -> None:
    """Set terrain category and z0 on the project's wind row."""
    await session.execute(
        text("UPDATE wind_climates SET terrain_category = COALESCE(:t, terrain_category), "
             "z0_m = COALESCE(:z, z0_m), updated_at = now() WHERE project_id = :p"),
        {"t": terrain, "z": z0, "p": project_id})


async def find_wind_row(session: AsyncSession, project_id: UUID) -> Mapping[str, Any]:
    """Return the wind row joined with the project's air density."""
    result = await session.execute(
        text("SELECT w.*, p.air_density_kg_m3 FROM wind_climates w "
             "JOIN projects p ON p.id = w.project_id WHERE w.project_id=:p"),
        {"p": project_id})
    return result.mappings().one()
