"""HTTP layer of the jobs domain."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.models.simulations.simulation_schemas import JobResponse
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.jobs.job_service import JobService, get_job_service

router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["jobs"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.get("/{job_id}", response_model=JobResponse, status_code=status.HTTP_200_OK)
async def read_job(
    job_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: JobService = Depends(get_job_service),
) -> JobResponse:
    """Return one job with progress, phase and error."""
    return await service.get(user, job_id)


@router.post("/{job_id}/cancel", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def cancel_job(
    job_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: JobService = Depends(get_job_service),
) -> JobResponse:
    """Cancel one job."""
    return await service.cancel(user, job_id)


@router.post("/{job_id}/retry", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def retry_job(
    job_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: JobService = Depends(get_job_service),
) -> JobResponse:
    """Re-queue a failed resumable job."""
    return await service.retry(user, job_id)
