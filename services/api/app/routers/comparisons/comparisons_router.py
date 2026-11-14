"""HTTP layer of the comparisons domain."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.models.comparisons.comparison_schemas import (
    ComparisonAreasResponse,
    ComparisonCheckResponse,
    ComparisonComfortResponse,
)
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.comparisons.comparison_service import (
    ComparisonService,
    get_comparison_service,
)

router = APIRouter(
    prefix="/api/v1/comparisons",
    tags=["comparisons"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.get("/check", response_model=ComparisonCheckResponse, status_code=status.HTTP_200_OK)
async def check_comparison(
    a: UUID, b: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: ComparisonService = Depends(get_comparison_service),
) -> ComparisonCheckResponse:
    """Say whether two results are comparable, or 422 with the differences."""
    await service.pair(user, a, b)
    return ComparisonCheckResponse(comparable=True)


@router.get("/areas", response_model=ComparisonAreasResponse, status_code=status.HTTP_200_OK)
async def compare_areas(
    a: UUID, b: UUID,
    k_accel: float | None = Query(default=None, gt=0),
    k_stagnation: float | None = Query(default=None, gt=0),
    dk_reduction: float | None = Query(default=None, lt=0),
    user: CurrentUser = Depends(require_current_user),
    service: ComparisonService = Depends(get_comparison_service),
) -> ComparisonAreasResponse:
    """Return acceleration, stagnation and reduction areas of two results."""
    return ComparisonAreasResponse(**await service.areas(user, a, b, k_accel, k_stagnation, dk_reduction))


@router.get("/comfort", response_model=ComparisonComfortResponse, status_code=status.HTTP_200_OK)
async def compare_comfort(
    study_a: UUID, study_b: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: ComparisonService = Depends(get_comparison_service),
) -> ComparisonComfortResponse:
    """Return both studies' Lawson comfort side by side."""
    return ComparisonComfortResponse(**await service.comfort(user, study_a, study_b))
