"""Pydantic models of the comfort domain."""

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel


class ComfortResponse(BaseModel):
    """The Comfort schema of openapi.yaml."""

    study_id: UUID
    status: Literal["pending", "running", "completed", "failed"]
    lawson_hash: str | None = None
    coverage: float = 0.0
    partial: bool = False
    class_areas: list[dict[str, Any]] = []
    safety_areas: list[dict[str, Any]] = []
    image: str | None = None
    field: str | None = None
