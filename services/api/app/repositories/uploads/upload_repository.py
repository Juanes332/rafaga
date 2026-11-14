"""Data access for the uploads table."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def insert_upload(
    session: AsyncSession, upload_id: UUID, project_id: UUID, kind: str,
    filename: str, path: str, size: int, sha256: str,
) -> None:
    """Record an uploaded file."""
    await session.execute(
        text(
            "INSERT INTO uploads (id, project_id, kind, filename, path, size_bytes, sha256) "
            "VALUES (:i, :p, :k, :f, :path, :s, :h)"
        ),
        {"i": upload_id, "p": project_id, "k": kind, "f": filename, "path": path,
         "s": size, "h": sha256},
    )


async def delete_upload(session: AsyncSession, upload_id: UUID) -> None:
    """Delete an upload row; its background plan cascades."""
    await session.execute(text("DELETE FROM uploads WHERE id = :i"), {"i": upload_id})
