"""Failures of the alternatives, facades and scene domains."""

from app.core.errors.error_contract import (
    ConflictError,
    NotFoundError,
    UnprocessableError,
)


class AlternativeNotFoundError(NotFoundError):
    """No alternative is visible to the caller under that identifier."""

    code = "alternative_not_found"
    default_message = "No alternative exists under that identifier."


class ElementNotFoundError(NotFoundError):
    """No facade element is visible to the caller under that identifier."""

    code = "element_not_found"
    default_message = "No facade element exists under that identifier."


class AlternativesLimitError(ConflictError):
    """The project already holds the maximum number of alternatives."""

    code = "alternatives_limit"
    default_message = "The alternatives limit has been reached."


class BaseUndeletableError(ConflictError):
    """The base alternative cannot be deleted."""

    code = "base_undeletable"
    default_message = "The base alternative cannot be deleted."


class BaseLockedError(ConflictError):
    """Changing the base case needs an explicit confirmation."""

    code = "base_locked"
    default_message = "The base case is locked while alternatives exist."


class NoBuildingsError(ConflictError):
    """The project has no buildings to attach anything to."""

    code = "no_buildings"
    default_message = "The project has no buildings."


class EdgeNotFoundError(UnprocessableError):
    """The building or edge does not exist in the project geometry."""

    code = "edge_not_found"
    default_message = "The building or edge does not exist."


class InvalidFacadeParamsError(UnprocessableError):
    """The facade parameters are unknown or not numeric."""

    code = "validation_error"
    default_message = "The facade parameters are invalid."
