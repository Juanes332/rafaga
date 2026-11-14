"""HTTP layer of project location."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.models.location.location_schemas import LocationRequest
from app.models.projects.project_schemas import ProjectResponse
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.location.location_service import LocationService, get_location_service

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/location",
    tags=["location"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.put("", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
async def put_location(
    project_id: UUID,
    body: LocationRequest,
    user: CurrentUser = Depends(require_current_user),
    service: LocationService = Depends(get_location_service),
) -> ProjectResponse:
    """Set the project location, resolving elevation when absent."""
    return await service.set_location(user, project_id, body)
