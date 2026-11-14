"""Failures of the results, comfort, comparisons, exports and reports domains."""

from app.core.errors.error_contract import (
    ConflictError,
    NotFoundError,
    UnprocessableError,
)


class ResultNotFoundError(NotFoundError):
    """No result is visible to the caller under that identifier."""

    code = "result_not_found"
    default_message = "No result exists under that identifier."


class FieldNotFoundError(NotFoundError):
    """The result has no such field."""

    code = "field_not_found"
    default_message = "The result has no field with that name."


class ImageNotFoundError(NotFoundError):
    """The result has no such image."""

    code = "image_not_found"
    default_message = "The result has no image with that name."


class ViewerNotAvailableError(NotFoundError):
    """The result is not a 3D volume."""

    code = "viewer_not_available"
    default_message = "The 3D viewer is only available for volume3d results."


class StudyNotFoundError(NotFoundError):
    """No study is visible to the caller under that identifier."""

    code = "study_not_found"
    default_message = "No study exists under that identifier."


class RoseMissingError(ConflictError):
    """The study has no ERA5 rose, so no comfort result exists."""

    code = "rose_missing"
    default_message = "Comfort needs an ERA5 wind rose; this project uses manual wind."


class ResultsIncomparableError(UnprocessableError):
    """Two results do not share a comparability key."""

    code = "results_incomparable"
    default_message = "The results are not comparable."


class ResultsMissingError(ConflictError):
    """No completed result exists to build the artefact from."""

    code = "results_missing"
    default_message = "There are no completed results to use."


class ExportNotFoundError(NotFoundError):
    """No export is visible to the caller under that identifier."""

    code = "export_not_found"
    default_message = "No export exists under that identifier."


class ExportNotReadyError(ConflictError):
    """The export file has not been rendered yet."""

    code = "export_not_ready"
    default_message = "The export file is not ready."


class ReportNotFoundError(NotFoundError):
    """No report is visible to the caller under that identifier."""

    code = "report_not_found"
    default_message = "No report exists under that identifier."


class ReportNotReadyError(ConflictError):
    """The report PDF has not been rendered yet."""

    code = "report_not_ready"
    default_message = "The report file is not ready."


class InvalidThresholdsError(UnprocessableError):
    """k_accel must be greater than k_stagnation, both positive."""

    code = "invalid_thresholds"
    default_message = "k_accel must be greater than k_stagnation and both positive."
