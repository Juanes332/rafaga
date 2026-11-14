"""Data access for the users table."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_COLUMNS = "id, email::text AS email, password_hash, role, created_at"


async def find_user_by_id(session: AsyncSession, user_id: UUID) -> Mapping[str, Any] | None:
    """Return the user row by id, or None."""
    result = await session.execute(
        text(f"SELECT {_COLUMNS} FROM users WHERE id = :id"), {"id": user_id}
    )
    return result.mappings().first()


async def find_user_by_email(session: AsyncSession, email: str) -> Mapping[str, Any] | None:
    """Return the user row by case-insensitive email, or None."""
    result = await session.execute(
        text(f"SELECT {_COLUMNS} FROM users WHERE email = :email"), {"email": email}
    )
    return result.mappings().first()


async def count_users(session: AsyncSession) -> int:
    """Return how many users exist."""
    return (await session.execute(text("SELECT count(*) FROM users"))).scalar_one()


async def insert_user(
    session: AsyncSession, email: str, password_hash: str, role: str
) -> Mapping[str, Any]:
    """Insert a user and return the stored row."""
    result = await session.execute(
        text(
            "INSERT INTO users (email, password_hash, role) "
            f"VALUES (:email, :hash, :role) RETURNING {_COLUMNS}"
        ),
        {"email": email, "hash": password_hash, "role": role},
    )
    return result.mappings().one()


async def list_users(session: AsyncSession) -> list[Mapping[str, Any]]:
    """Return every user, oldest first."""
    result = await session.execute(
        text(f"SELECT {_COLUMNS} FROM users ORDER BY created_at, email")
    )
    return list(result.mappings().all())


async def delete_user(session: AsyncSession, user_id: UUID) -> None:
    """Delete a user row; dependent shares cascade."""
    await session.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})


async def lock_user_creation(session: AsyncSession) -> None:
    """Serialize first-run setup across concurrent requests."""
    await session.execute(text("SELECT pg_advisory_xact_lock(727274)"))
