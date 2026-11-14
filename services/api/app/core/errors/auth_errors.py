"""Failures of the auth and users domains."""

from fastapi import status

from app.core.errors.error_contract import (
    AppError,
    ConflictError,
    NotFoundError,
    UnprocessableError,
)


class InvalidCredentialsError(AppError):
    """Email unknown or password wrong; the two are indistinguishable."""

    status_code = status.HTTP_401_UNAUTHORIZED
    code = "invalid_credentials"
    default_message = "The email or password is incorrect."


class SetupAlreadyDoneError(ConflictError):
    """First-run setup was attempted after a user already exists."""

    code = "setup_already_done"
    default_message = "The initial setup has already been completed."


class PasswordTooShortError(UnprocessableError):
    """The password has fewer than ten characters."""

    code = "password_too_short"
    default_message = "The password must have at least 10 characters."


class EmailTakenError(ConflictError):
    """Another user already owns that email."""

    code = "email_taken"
    default_message = "A user with that email already exists."


class CannotDeleteSelfError(ConflictError):
    """An architect tried to delete their own account."""

    code = "cannot_delete_self"
    default_message = "A user cannot delete their own account."


class UserNotFoundError(NotFoundError):
    """No user exists under that identifier."""

    code = "user_not_found"
    default_message = "No user exists under that identifier."
