"""Data access for studies, comfort results and light-lane jobs."""

import json
from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

Row = Mapping[str, Any]


async def find_study(session: AsyncSession, study_id: UUID) -> Row | None:
    """Return the study row by id, whoever owns the project."""
    r = await session.execute(text("SELECT * FROM studies WHERE id = :i"), {"i": study_id})
    return r.mappings().first()


async def find_comfort(session: AsyncSession, study_id: UUID, lawson_hash: str) -> Row | None:
    """Return the comfort result stored under a Lawson hash."""
    r = await session.execute(
        text("SELECT * FROM comfort_results WHERE study_id = :s AND lawson_hash = :h"),
        {"s": study_id, "h": lawson_hash})
    return r.mappings().first()


async def find_aggregate_job(session: AsyncSession, study_id: UUID, lawson_hash: str) -> Row | None:
    """Return the newest aggregate job of a study for a Lawson hash."""
    r = await session.execute(
        text("SELECT id, status FROM jobs WHERE study_id = :s AND kind = 'aggregate' "
             "AND payload->>'lawson_hash' = :h ORDER BY created_at DESC LIMIT 1"),
        {"s": study_id, "h": lawson_hash})
    return r.mappings().first()


async def insert_light_job(
    session: AsyncSession, *, project_id: UUID, owner_id: UUID, study_id: UUID | None,
    kind: str, payload: dict[str, Any],
) -> UUID:
    """Insert a queued light-lane job (priority 10); the trigger notifies."""
    r = await session.execute(
        text("INSERT INTO jobs (study_id, project_id, owner_id, kind, lane, priority, payload) "
             "VALUES (:s, :p, :o, :k, 'light', 10, CAST(:pl AS jsonb)) RETURNING id"),
        {"s": study_id, "p": project_id, "o": owner_id, "k": kind,
         "pl": json.dumps(payload, separators=(",", ":"))})
    return r.scalar_one()
