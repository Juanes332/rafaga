"""Failures of the simulations, jobs, settings and templates domains."""

from fastapi import status

from app.core.errors.error_contract import (
    AppError,
    ConflictError,
    NotFoundError,
    UnprocessableError,
)


class AlternativeNotFoundForRunError(NotFoundError):
    """No alternative is visible to the caller (simulation entry point)."""

    code = "alternative_not_found"
    default_message = "No alternative exists under that identifier."


class StudyNotFoundError(NotFoundError):
    """No study is visible to the caller under that identifier."""

    code = "study_not_found"
    default_message = "No study exists under that identifier."


class JobNotFoundError(NotFoundError):
    """No job is visible to the caller under that identifier."""

    code = "job_not_found"
    default_message = "No job exists under that identifier."


class TemplateNotFoundError(NotFoundError):
    """No template is visible to the caller under that identifier."""

    code = "template_not_found"
    default_message = "No template exists under that identifier."


class TemplateContainsLocationError(UnprocessableError):
    """A template payload carries a location key (BR-18)."""

    code = "template_contains_location"
    default_message = "Templates must not contain location data."


class LocationMissingError(ConflictError):
    """The project has no complete location yet."""

    code = "location_missing"
    default_message = "The project needs a location before simulating."


class WindMissingError(ConflictError):
    """Manual wind lacks direction or speed."""

    code = "wind_missing"
    default_message = "The project's manual wind is incomplete."


class RoseMissingError(ConflictError):
    """The wind source is era5 but no rose was fetched."""

    code = "rose_missing"
    default_message = "The project has no wind rose."


class DirectionsRequiredError(UnprocessableError):
    """No simulation direction could be resolved."""

    code = "directions_required"
    default_message = "At least one wind direction is required."


class GeometryInvalidError(UnprocessableError):
    """The base geometry cannot be simulated."""

    code = "geometry_invalid"
    default_message = "The geometry has issues that block the simulation."


class MeshTooLargeError(UnprocessableError):
    """The grid does not fit the device and auto-coarsening is off."""

    code = "mesh_too_large"
    default_message = "The grid does not fit the device memory."


class BuildingsTooSmallError(UnprocessableError):
    """A building is narrower than four cells after coarsening."""

    code = "buildings_too_small"
    default_message = "The smallest building is narrower than 4 cells."


class PayloadTooLargeError(AppError):
    """The job payload exceeds the 20 MB limit."""

    status_code = status.HTTP_413_CONTENT_TOO_LARGE
    code = "payload_too_large"
    default_message = "The job payload exceeds the size limit."


class JobNotCancellableError(ConflictError):
    """The job already finished."""

    code = "job_not_cancellable"
    default_message = "The job has already finished."


class JobNotRetryableError(ConflictError):
    """Only failed resumable jobs can be retried."""

    code = "job_not_retryable"
    default_message = "The job cannot be retried."


class TemplateInvalidError(UnprocessableError):
    """A template payload or its application violates a range rule."""

    code = "validation_error"
    default_message = "The template content is invalid."
