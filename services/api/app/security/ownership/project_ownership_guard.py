"""Answer "is this project yours", never "who are you"."""

from collections.abc import Callable, Mapping
from typing import Any, Literal

from pydantic import BaseModel

from app.core.errors.error_contract import AppError, ForbiddenError
from app.security.jwt.jwt_guard import CurrentUser


class ProjectAccess(BaseModel):
    """What the caller may do on one project."""

    project_id: Any
    owner_id: Any
    role_on_project: Literal["owner", "reviewer"]


def require_project_access(
    project: Mapping[str, Any] | None,
    has_share: bool,
    user: CurrentUser,
    *,
    write: bool,
    not_found: Callable[[], AppError],
) -> ProjectAccess:
    """Return the caller's access, or refuse it.

    A missing project and a foreign unshared one raise the same
    error (RFC 9110 15.5.5). A shared reviewer attempting a write
    gets 403: the project is visible to them, the role is lacking.
    """
    is_owner = project is not None and project["owner_id"] == user.id
    if project is None or not (is_owner or has_share):
        raise not_found()
    if write and (not is_owner or user.role != "architect"):
        raise ForbiddenError()
    return ProjectAccess(
        project_id=project["id"],
        owner_id=project["owner_id"],
        role_on_project="owner" if is_owner else "reviewer",
    )
