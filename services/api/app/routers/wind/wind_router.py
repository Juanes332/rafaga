"""HTTP layer of the wind domain."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.models.wind.wind_schemas import Era5Request, WindClimateResponse, WindPatchRequest
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.wind.wind_service import WindService, get_wind_service

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/wind",
    tags=["wind"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.get("", response_model=WindClimateResponse, status_code=status.HTTP_200_OK)
async def read_wind(
    project_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: WindService = Depends(get_wind_service),
) -> WindClimateResponse:
    """Return the project's wind climate."""
    return await service.get(user, project_id)


@router.patch("", response_model=WindClimateResponse, status_code=status.HTTP_200_OK)
async def patch_wind(
    project_id: UUID,
    body: WindPatchRequest,
    user: CurrentUser = Depends(require_current_user),
    service: WindService = Depends(get_wind_service),
) -> WindClimateResponse:
    """Update wind source, manual wind and roughness."""
    return await service.patch(user, project_id, body)


@router.post("/era5", response_model=WindClimateResponse, status_code=status.HTTP_200_OK)
async def fetch_era5(
    project_id: UUID,
    body: Era5Request | None = None,
    user: CurrentUser = Depends(require_current_user),
    service: WindService = Depends(get_wind_service),
) -> WindClimateResponse:
    """Fetch the ERA5 wind rose for a located project."""
    return await service.fetch_era5(user, project_id, body or Era5Request())
