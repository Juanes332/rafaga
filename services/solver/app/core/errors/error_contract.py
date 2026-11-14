"""The single shape every error response takes."""

from fastapi import status
from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    """The body of every failed response, whatever the cause."""

    code: str = Field(..., description="Stable machine-readable identifier")
    message: str = Field(..., description="Human-readable, safe to surface")


class AppError(Exception):
    """Base for every HTTP failure this service reports on purpose."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_error"

    def __init__(self, message: str) -> None:
        """Store the client-facing message."""
        super().__init__(message)
        self.message = message
        self.headers: dict[str, str] = {}

    def as_body(self) -> ErrorBody:
        """Return the wire representation of this error."""
        return ErrorBody(code=self.code, message=self.message)
