"""HTTP layer of the comfort domain."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.models.comfort.comfort_schemas import ComfortResponse
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.comfort.comfort_service import ComfortService, get_comfort_service

router = APIRouter(
    prefix="/api/v1/simulations/{study_id}/comfort",
    tags=["comfort"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.get("", response_model=ComfortResponse, status_code=status.HTTP_200_OK)
async def read_comfort(
    study_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: ComfortService = Depends(get_comfort_service),
) -> ComfortResponse:
    """Return the comfort result for the caller's current Lawson table."""
    return await service.get(user, study_id)


@router.post("/recompute", response_model=ComfortResponse, status_code=status.HTTP_202_ACCEPTED)
async def recompute_comfort(
    study_id: UUID,
    response: Response,
    user: CurrentUser = Depends(require_current_user),
    service: ComfortService = Depends(get_comfort_service),
) -> ComfortResponse:
    """Enqueue an aggregate job, or return the existing result with 200."""
    body, code = await service.recompute(user, study_id)
    response.status_code = code
    return body
