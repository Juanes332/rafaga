"""Failures the rate limiter can report."""

from fastapi import status

from app.core.errors.error_contract import AppError


class RateLimitedError(AppError):
    """The caller spent its budget for the current window."""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "rate_limited"

    def __init__(self, retry_after: int) -> None:
        """Advertise how many seconds until the window resets."""
        super().__init__("Too many requests. Retry after the advertised delay.")
        self.headers = {"Retry-After": str(retry_after)}
