"""Pydantic models of the shares domain."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ShareResponse(BaseModel):
    """A reviewer holding access to a project."""

    user_id: UUID
    email: str
    created_at: datetime | None = None
