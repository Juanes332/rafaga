"""The single shape every error response takes."""

from typing import Any

from fastapi import status
from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    """The body of every failed response, whatever the cause."""

    code: str = Field(..., description="Stable machine-readable identifier")
    message: str = Field(..., description="Technical English message")
    details: dict[str, Any] | None = None
    hint: str | None = None


class AppError(Exception):
    """Base for every failure this service reports on purpose.

    Raising a subclass is the only supported way to fail a request,
    because it keeps the HTTP status and the body in agreement.
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_error"
    default_message: str = "The request could not be completed."

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
        hint: str | None = None,
    ) -> None:
        """Store the client-facing message, details and hint."""
        self.message = message or self.default_message
        super().__init__(self.message)
        self.details = details
        self.hint = hint
        self.headers: dict[str, str] = {}

    def as_body(self) -> dict[str, Any]:
        """Return the wire representation, omitting empty optionals."""
        body = ErrorBody(
            code=self.code, message=self.message, details=self.details, hint=self.hint
        )
        return body.model_dump(exclude_none=True)


class NotFoundError(AppError):
    """The addressed resource does not exist or is not visible."""

    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ForbiddenError(AppError):
    """The caller is authenticated but lacks the role."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"
    default_message = "The caller's role does not allow this action."


class ConflictError(AppError):
    """The request collides with the current state of the resource."""

    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


class UnprocessableError(AppError):
    """The payload is well formed but semantically unacceptable."""

    status_code = 422
    code = "unprocessable"


class UnavailableError(AppError):
    """An upstream dependency is unreachable."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "unavailable"
