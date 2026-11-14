"""HTTP layer of the reports domain."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse

from app.models.exports.export_schemas import (
    ReportAcceptedResponse,
    ReportCreateRequest,
    ReportResponse,
)
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.reports.report_service import ReportService, get_report_service

router = APIRouter(
    prefix="/api/v1",
    tags=["reports"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.post("/projects/{project_id}/reports", response_model=ReportAcceptedResponse,
             status_code=status.HTTP_202_ACCEPTED)
async def create_report(
    project_id: UUID,
    body: ReportCreateRequest,
    user: CurrentUser = Depends(require_current_user),
    service: ReportService = Depends(get_report_service),
) -> ReportAcceptedResponse:
    """Enqueue a PDF report job."""
    return await service.create(user, project_id, body)


@router.get("/projects/{project_id}/reports", response_model=list[ReportResponse],
            status_code=status.HTTP_200_OK)
async def list_reports(
    project_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: ReportService = Depends(get_report_service),
) -> list[ReportResponse]:
    """List the project's reports."""
    return await service.list(user, project_id)


@router.get("/reports/{report_id}", response_model=ReportResponse, status_code=status.HTTP_200_OK)
async def read_report(
    report_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: ReportService = Depends(get_report_service),
) -> ReportResponse:
    """Return the report status."""
    return await service.get(user, report_id)


@router.get("/reports/{report_id}/file", status_code=status.HTTP_200_OK)
async def read_report_file(
    report_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: ReportService = Depends(get_report_service),
) -> FileResponse:
    """Stream the PDF as an attachment."""
    path, name = await service.file(user, report_id)
    return FileResponse(path, media_type="application/pdf", filename=name)
