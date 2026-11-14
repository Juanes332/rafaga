"""HTTP layer of the geometry domain."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status

from app.models.geometry.geometry_schemas import (
    GeometryPutRequest,
    GeometryResponse,
    GeometryValidateRequest,
    GeometryValidationResponse,
    ImportReportResponse,
)
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.geometry.geometry_import_service import (
    GeometryImportService,
    get_geometry_import_service,
)
from app.services.geometry.geometry_service import GeometryService, get_geometry_service

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/geometry",
    tags=["geometry"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.get("", response_model=GeometryResponse, status_code=status.HTTP_200_OK)
async def read_geometry(
    project_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: GeometryService = Depends(get_geometry_service),
) -> GeometryResponse:
    """Return the base-case buildings with their issues."""
    return await service.get(user, project_id)


@router.put("", response_model=GeometryResponse, status_code=status.HTTP_200_OK)
async def replace_geometry(
    project_id: UUID,
    body: GeometryPutRequest,
    user: CurrentUser = Depends(require_current_user),
    service: GeometryService = Depends(get_geometry_service),
) -> GeometryResponse:
    """Replace the building set under optimistic locking."""
    return await service.put(user, project_id, body)


@router.post(
    "/validate", response_model=GeometryValidationResponse, status_code=status.HTTP_200_OK
)
async def validate_geometry(
    project_id: UUID,
    body: GeometryValidateRequest,
    user: CurrentUser = Depends(require_current_user),
    service: GeometryService = Depends(get_geometry_service),
) -> GeometryValidationResponse:
    """Validate submitted or stored buildings without saving."""
    return await service.validate(user, project_id, body.buildings)


@router.post("/imports", response_model=ImportReportResponse, status_code=status.HTTP_201_CREATED)
async def import_geometry(
    project_id: UUID,
    request: Request,
    file: Annotated[UploadFile, File()],
    unit: Annotated[Literal["auto", "m", "cm", "mm", "ft"], Form()] = "auto",
    mode: Annotated[Literal["append", "replace"], Form()] = "append",
    center: Annotated[bool, Form()] = True,
    user: CurrentUser = Depends(require_current_user),
    service: GeometryImportService = Depends(get_geometry_import_service),
) -> ImportReportResponse:
    """Import a DXF, STL, OBJ or IFC file into the base case."""
    declared = int(request.headers.get("content-length") or 0)
    return await service.import_file(user, project_id, file, declared, unit, mode, center)
