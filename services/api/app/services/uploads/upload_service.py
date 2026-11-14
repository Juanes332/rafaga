"""Uploads domain: size-checked reads and persistence on the data volume."""

import hashlib
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.config import Settings
from app.core.errors.geometry_errors import UploadTooLargeError
from app.repositories.uploads import upload_repository as repo

CHUNK = 1024 * 1024


async def read_limited(
    upload: UploadFile, limit_mb: int, declared_length: int = 0
) -> bytes:
    """Read an upload into memory, refusing it past the limit.

    Nothing is persisted here, so an oversized file leaves no trace.
    """
    limit = limit_mb * 1024 * 1024
    refusal = UploadTooLargeError(details={"limit_mb": limit_mb, "limit_bytes": limit})
    if declared_length > limit + 64 * 1024:
        raise refusal
    data = bytearray()
    while chunk := await upload.read(CHUNK):
        data.extend(chunk)
        if len(data) > limit:
            raise refusal
    return bytes(data)


async def store_upload(
    session: AsyncSession, settings: Settings, project_id: UUID,
    kind: str, filename: str, data: bytes,
) -> UUID:
    """Write the file under uploads/<project>/ and record its row."""
    upload_id = uuid4()
    suffix = Path(filename).suffix.lower()
    rel = f"uploads/{project_id}/{upload_id}{suffix}"
    target = Path(settings.data_dir) / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    await repo.insert_upload(
        session, upload_id, project_id, kind, Path(filename).name[:255], rel,
        len(data), hashlib.sha256(data).hexdigest(),
    )
    return upload_id


def remove_file(settings: Settings, rel_path: str) -> None:
    """Delete an uploaded file, ignoring a missing one."""
    (Path(settings.data_dir) / rel_path).unlink(missing_ok=True)
