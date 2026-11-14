"""HTTP layer of the scene domain."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.scene.scene_service import SceneService, get_scene_service

router = APIRouter(
    prefix="/api/v1/alternatives",
    tags=["scene"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.get("/{alternative_id}/scene", response_model=dict[str, Any], status_code=status.HTTP_200_OK)
async def read_scene(
    alternative_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: SceneService = Depends(get_scene_service),
) -> dict[str, Any]:
    """Return the compiled canonical scene of an alternative."""
    return await service.compile_for_alternative(user, alternative_id)
