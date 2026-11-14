"""Failures of the projects and shares domains."""

from app.core.errors.error_contract import NotFoundError


class ProjectNotFoundError(NotFoundError):
    """No project is visible to the caller under that identifier.

    A foreign project and a missing one raise this with the same
    message, so the two response bodies are byte-identical.
    """

    code = "project_not_found"
    default_message = "No project exists under that identifier."
