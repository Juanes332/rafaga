"""HTTP layer of the results domain."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import FileResponse

from app.models.results.result_schemas import (
    ResultResponse,
    Viewer3DResponse,
    ZoneAreasResponse,
)
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.results.result_service import ResultService, get_result_service

router = APIRouter(
    prefix="/api/v1/results",
    tags=["results"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.get("/{result_id}", response_model=ResultResponse, status_code=status.HTTP_200_OK)
async def read_result(
    result_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: ResultService = Depends(get_result_service),
) -> ResultResponse:
    """Return the result metadata."""
    return await service.get(user, result_id)


@router.get("/{result_id}/fields/{field_name:path}", status_code=status.HTTP_200_OK)
async def read_field(
    result_id: UUID,
    field_name: str,
    user: CurrentUser = Depends(require_current_user),
    service: ResultService = Depends(get_result_service),
) -> FileResponse:
    """Stream a raw field with its shape and dtype headers."""
    path, entry = await service.field_file(user, result_id, field_name)
    headers = {"X-Field-Shape": ",".join(map(str, entry["shape"])), "X-Field-Dtype": entry["dtype"]}
    return FileResponse(path, media_type="application/octet-stream", headers=headers)


@router.get("/{result_id}/images/{image_name:path}", status_code=status.HTTP_200_OK)
async def read_image(
    result_id: UUID,
    image_name: str,
    user: CurrentUser = Depends(require_current_user),
    service: ResultService = Depends(get_result_service),
) -> FileResponse:
    """Stream a preview PNG."""
    return FileResponse(await service.image_file(user, result_id, image_name), media_type="image/png")


@router.get("/{result_id}/zones", response_model=ZoneAreasResponse, status_code=status.HTTP_200_OK)
async def read_zones(
    result_id: UUID,
    k_accel: float | None = Query(default=None, gt=0),
    k_stagnation: float | None = Query(default=None, gt=0),
    user: CurrentUser = Depends(require_current_user),
    service: ResultService = Depends(get_result_service),
) -> ZoneAreasResponse:
    """Return zone areas for the requested thresholds."""
    return await service.zones(user, result_id, k_accel, k_stagnation)


@router.get("/{result_id}/viewer3d", response_model=Viewer3DResponse, status_code=status.HTTP_200_OK)
async def read_viewer3d(
    result_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: ResultService = Depends(get_result_service),
) -> Viewer3DResponse:
    """Return the 3D viewer data of a volume result."""
    return await service.viewer3d(user, result_id)


@router.get("/{result_id}/download", status_code=status.HTTP_200_OK)
async def download_result(
    result_id: UUID,
    format: Literal["npz", "csv"] = Query(),
    user: CurrentUser = Depends(require_current_user),
    service: ResultService = Depends(get_result_service),
) -> Response:
    """Download fields.npz or a CSV of the fluid cells."""
    disposition = {"Content-Disposition": f'attachment; filename="result-{result_id}.{format}"'}
    if format == "npz":
        path = await service.npz_path(user, result_id)
        return FileResponse(path, media_type="application/octet-stream", headers=disposition)
    body = await service.csv_text(user, result_id)
    return Response(body, media_type="text/csv", headers=disposition)
