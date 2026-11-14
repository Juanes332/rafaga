"""HTTP layer of the facades domain."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.models.facades.facade_schemas import (
    FacadeElementCreateRequest,
    FacadeElementPatchRequest,
    FacadeElementResponse,
    FacadeElementWithAdjustments,
    FacadeStrategyResponse,
)
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.facades.facade_service import (
    FacadeService,
    get_facade_service,
    list_strategies,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["facades"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.get("/facade-strategies", response_model=list[FacadeStrategyResponse],
            status_code=status.HTTP_200_OK)
async def read_facade_strategies() -> list[FacadeStrategyResponse]:
    """Return the strategy catalogue (ranges and defaults)."""
    return list_strategies()


@router.get("/alternatives/{alternative_id}/facade-elements",
            response_model=list[FacadeElementResponse], status_code=status.HTTP_200_OK)
async def list_facade_elements(
    alternative_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: FacadeService = Depends(get_facade_service),
) -> list[FacadeElementResponse]:
    """List an alternative's facade elements."""
    return await service.list(user, alternative_id)


@router.post("/alternatives/{alternative_id}/facade-elements",
             response_model=FacadeElementWithAdjustments, status_code=status.HTTP_201_CREATED)
async def create_facade_element(
    alternative_id: UUID, body: FacadeElementCreateRequest, confirm_base_change: bool = False,
    user: CurrentUser = Depends(require_current_user),
    service: FacadeService = Depends(get_facade_service),
) -> FacadeElementWithAdjustments:
    """Create a facade element on a building edge."""
    return await service.create(user, alternative_id, body, confirm_base_change)


@router.patch("/facade-elements/{element_id}", response_model=FacadeElementWithAdjustments,
              status_code=status.HTTP_200_OK)
async def patch_facade_element(
    element_id: UUID, body: FacadeElementPatchRequest,
    user: CurrentUser = Depends(require_current_user),
    service: FacadeService = Depends(get_facade_service),
) -> FacadeElementWithAdjustments:
    """Update an element's params with clamping."""
    return await service.patch(user, element_id, body.params, body.confirm_base_change)


@router.delete("/facade-elements/{element_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_facade_element(
    element_id: UUID, confirm_base_change: bool = False,
    user: CurrentUser = Depends(require_current_user),
    service: FacadeService = Depends(get_facade_service),
) -> Response:
    """Delete a facade element."""
    await service.delete(user, element_id, confirm_base_change)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
