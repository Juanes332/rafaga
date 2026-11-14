"""HTTP layer of project sharing."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.models.shares.share_schemas import ShareResponse
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.shares.share_service import ShareService, get_share_service

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/shares",
    tags=["shares"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.get("", response_model=list[ShareResponse], status_code=status.HTTP_200_OK)
async def list_shares(
    project_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: ShareService = Depends(get_share_service),
) -> list[ShareResponse]:
    """List users with access to the project."""
    return await service.list(user, project_id)


@router.put("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def grant_share(
    project_id: UUID,
    user_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: ShareService = Depends(get_share_service),
) -> Response:
    """Grant a user read access."""
    await service.grant(user, project_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share(
    project_id: UUID,
    user_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: ShareService = Depends(get_share_service),
) -> Response:
    """Revoke a user's access."""
    await service.revoke(user, project_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
