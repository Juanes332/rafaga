"""Role checks: what a role may do, not whose row it is."""

from fastapi import Depends

from app.core.errors.error_contract import ForbiddenError
from app.security.jwt.jwt_guard import CurrentUser, require_current_user


def require_architect(user: CurrentUser = Depends(require_current_user)) -> CurrentUser:
    """Return the caller when they hold the architect role, else 403."""
    if user.role != "architect":
        raise ForbiddenError()
    return user
