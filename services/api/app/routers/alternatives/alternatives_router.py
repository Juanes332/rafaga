"""HTTP layer of the alternatives domain."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.models.alternatives.alternative_schemas import (
    AlternativeCreateRequest,
    AlternativePatchRequest,
    AlternativeResponse,
)
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.alternatives.alternative_service import (
    AlternativeService,
    get_alternative_service,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["alternatives"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.get("/projects/{project_id}/alternatives", response_model=list[AlternativeResponse],
            status_code=status.HTTP_200_OK)
async def list_alternatives(
    project_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: AlternativeService = Depends(get_alternative_service),
) -> list[AlternativeResponse]:
    """List alternatives, base first."""
    return await service.list(user, project_id)


@router.post("/projects/{project_id}/alternatives", response_model=AlternativeResponse,
             status_code=status.HTTP_201_CREATED)
async def create_alternative(
    project_id: UUID, body: AlternativeCreateRequest,
    user: CurrentUser = Depends(require_current_user),
    service: AlternativeService = Depends(get_alternative_service),
) -> AlternativeResponse:
    """Create an alternative copying facade elements."""
    return await service.create(user, project_id, body)


@router.patch("/alternatives/{alternative_id}", response_model=AlternativeResponse,
              status_code=status.HTTP_200_OK)
async def patch_alternative(
    alternative_id: UUID, body: AlternativePatchRequest,
    user: CurrentUser = Depends(require_current_user),
    service: AlternativeService = Depends(get_alternative_service),
) -> AlternativeResponse:
    """Rename or reorder an alternative."""
    return await service.patch(user, alternative_id, body)


@router.delete("/alternatives/{alternative_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alternative(
    alternative_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: AlternativeService = Depends(get_alternative_service),
) -> Response:
    """Delete a non-base alternative."""
    await service.delete(user, alternative_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
