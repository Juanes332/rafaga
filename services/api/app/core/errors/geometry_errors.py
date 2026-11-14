"""Failures of the geometry, uploads and backgrounds domains."""

from fastapi import status

from app.core.errors.error_contract import (
    AppError,
    ConflictError,
    NotFoundError,
    UnprocessableError,
)


class VersionConflictError(ConflictError):
    """The submitted expected_version is stale."""

    code = "version_conflict"
    default_message = "The geometry was modified by someone else; reload it."


class BaseLockedError(ConflictError):
    """Alternatives exist, so changing the base needs confirmation."""

    code = "base_locked"
    default_message = "Alternatives exist; confirm the change to the base case."


class ImportFailedError(UnprocessableError):
    """The file could not be read as geometry."""

    code = "import_failed"
    default_message = "The file could not be imported."


class UnsupportedFormatError(UnprocessableError):
    """The file extension or content is not a supported format."""

    code = "unsupported_format"
    default_message = "The file format is not supported."


class UploadTooLargeError(AppError):
    """The upload exceeds the size limit for its kind."""

    status_code = status.HTTP_413_CONTENT_TOO_LARGE
    code = "upload_too_large"
    default_message = "The file exceeds the maximum allowed size."


class BackgroundNotFoundError(NotFoundError):
    """No background plan is visible under that identifier."""

    code = "background_not_found"
    default_message = "No background plan exists under that identifier."


class PageNotFoundError(NotFoundError):
    """The requested page does not exist in the background."""

    code = "page_not_found"
    default_message = "The background has no such page."
