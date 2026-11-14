"""HTTP layer of the projects domain."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.models.projects.project_schemas import (
    ProjectCreateRequest,
    ProjectPatchRequest,
    ProjectResponse,
    ProjectSummaryResponse,
)
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.security.roles.role_guard import require_architect
from app.services.projects.project_service import ProjectService, get_project_service

router = APIRouter(
    prefix="/api/v1/projects",
    tags=["projects"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.get("", response_model=list[ProjectSummaryResponse], status_code=status.HTTP_200_OK)
async def list_projects(
    user: CurrentUser = Depends(require_current_user),
    service: ProjectService = Depends(get_project_service),
) -> list[ProjectSummaryResponse]:
    """List projects owned by or shared with the caller."""
    return await service.list_for(user)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreateRequest,
    user: CurrentUser = Depends(require_architect),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Create an empty project (architects only)."""
    return await service.create(user, body.name)


@router.get("/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
async def read_project(
    project_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Return one project."""
    return await service.get(user, project_id)


@router.patch("/{project_id}", response_model=ProjectResponse, status_code=status.HTTP_200_OK)
async def patch_project(
    project_id: UUID,
    body: ProjectPatchRequest,
    user: CurrentUser = Depends(require_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Rename a project or set its analysis height."""
    return await service.patch(user, project_id, body)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: ProjectService = Depends(get_project_service),
) -> Response:
    """Delete a project and its files."""
    await service.delete(user, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{project_id}/duplicate",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_project(
    project_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Duplicate a project without jobs or results."""
    return await service.duplicate(user, project_id)
