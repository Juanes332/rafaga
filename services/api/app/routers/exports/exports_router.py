"""HTTP layer of the exports domain."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse

from app.models.exports.export_schemas import (
    ExportAcceptedResponse,
    ExportCreateRequest,
    ExportResponse,
)
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.exports.export_service import ExportService, get_export_service

router = APIRouter(
    prefix="/api/v1/exports",
    tags=["exports"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.post("", response_model=ExportAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_export(
    body: ExportCreateRequest,
    user: CurrentUser = Depends(require_current_user),
    service: ExportService = Depends(get_export_service),
) -> ExportAcceptedResponse:
    """Enqueue a PNG export render job."""
    return await service.create(user, body)


@router.get("/{export_id}", response_model=ExportResponse, status_code=status.HTTP_200_OK)
async def read_export(
    export_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: ExportService = Depends(get_export_service),
) -> ExportResponse:
    """Return the export status."""
    return await service.get(user, export_id)


@router.get("/{export_id}/file", status_code=status.HTTP_200_OK)
async def read_export_file(
    export_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: ExportService = Depends(get_export_service),
) -> FileResponse:
    """Stream the rendered PNG as an attachment."""
    path = await service.file(user, export_id)
    return FileResponse(path, media_type="image/png", filename=f"rafaga-export-{export_id}.png")
