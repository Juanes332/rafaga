"""Enqueue light-lane jobs with the payload size limit applied."""

import json
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.config import Settings
from app.core.errors.error_contract import UnprocessableError
from app.repositories.comfort.comfort_repository import insert_light_job


class PayloadTooLargeError(UnprocessableError):
    """The job payload exceeds the contract's 20 MB limit."""

    code = "payload_too_large"
    default_message = "The job payload exceeds the allowed size."


async def enqueue_light_job(
    session: AsyncSession, settings: Settings, *, project_id: UUID, owner_id: UUID,
    study_id: UUID | None, kind: str, payload: dict[str, Any],
) -> UUID:
    """Insert a light job unless its payload is above the 20 MB limit."""
    if len(json.dumps(payload)) > settings.max_payload_mb * 1024 * 1024:
        raise PayloadTooLargeError()
    return await insert_light_job(session, project_id=project_id, owner_id=owner_id,
                                  study_id=study_id, kind=kind, payload=payload)
