"""Direct-database helpers for rows owned by other batches."""

from typing import Any

from httpx import AsyncClient
from sqlalchemy import text


async def add_alternative(client: AsyncClient, project_id: str) -> None:
    """Insert a derived alternative straight into the database."""
    app: Any = client._transport.app  # noqa: SLF001
    async with app.state.session_factory() as s:
        await s.execute(text(
            "INSERT INTO alternatives (project_id, name, position) VALUES (:p, 'alt', 1)"),
            {"p": project_id})
        await s.commit()
