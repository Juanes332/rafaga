"""HTTP layer of the backgrounds domain."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Request, Response, UploadFile, status

from app.models.backgrounds.background_schemas import (
    BackgroundPatchRequest,
    BackgroundResponse,
)
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.backgrounds.background_service import (
    BackgroundService,
    get_background_service,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["backgrounds"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.post(
    "/projects/{project_id}/backgrounds",
    response_model=BackgroundResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_background(
    project_id: UUID,
    request: Request,
    file: Annotated[UploadFile, File()],
    user: CurrentUser = Depends(require_current_user),
    service: BackgroundService = Depends(get_background_service),
) -> BackgroundResponse:
    """Upload a PNG, JPG or PDF plan."""
    declared = int(request.headers.get("content-length") or 0)
    return await service.create(user, project_id, file, declared)


@router.get(
    "/projects/{project_id}/backgrounds",
    response_model=list[BackgroundResponse],
    status_code=status.HTTP_200_OK,
)
async def list_backgrounds(
    project_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: BackgroundService = Depends(get_background_service),
) -> list[BackgroundResponse]:
    """List a project's background plans."""
    return await service.list(user, project_id)


@router.get(
    "/backgrounds/{background_id}/pages/{page}.png",
    response_class=Response,
    status_code=status.HTTP_200_OK,
)
async def read_background_page(
    background_id: UUID,
    page: int,
    user: CurrentUser = Depends(require_current_user),
    service: BackgroundService = Depends(get_background_service),
) -> Response:
    """Return one page rasterized to PNG."""
    png = await service.page_png(user, background_id, page)
    return Response(content=png, media_type="image/png")


@router.patch(
    "/backgrounds/{background_id}",
    response_model=BackgroundResponse,
    status_code=status.HTTP_200_OK,
)
async def patch_background(
    background_id: UUID,
    body: BackgroundPatchRequest,
    user: CurrentUser = Depends(require_current_user),
    service: BackgroundService = Depends(get_background_service),
) -> BackgroundResponse:
    """Store calibration, transform, page or opacity."""
    return await service.patch(user, background_id, body)


@router.delete("/backgrounds/{background_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_background(
    background_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: BackgroundService = Depends(get_background_service),
) -> Response:
    """Delete a plan and its file."""
    await service.delete(user, background_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
