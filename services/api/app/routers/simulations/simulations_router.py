"""HTTP layer of the simulations domain."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.models.simulations.simulation_schemas import (
    EstimateRequest,
    EstimateResponse,
    SimulationCreateRequest,
    StudyResponse,
    StudySummaryResponse,
)
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.simulations.simulation_service import (
    SimulationService,
    get_simulation_service,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["simulations"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.post("/simulations/estimate", response_model=EstimateResponse, status_code=status.HTTP_200_OK)
async def estimate_simulation(
    body: EstimateRequest,
    user: CurrentUser = Depends(require_current_user),
    service: SimulationService = Depends(get_simulation_service),
) -> EstimateResponse:
    """Estimate memory, ETA and coarsening for a run."""
    return await service.estimate(user, body)


@router.post("/simulations", response_model=StudyResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_simulation(
    body: SimulationCreateRequest,
    user: CurrentUser = Depends(require_current_user),
    service: SimulationService = Depends(get_simulation_service),
) -> StudyResponse:
    """Queue a study: one heavy job per direction."""
    return await service.create(user, body)


@router.get(
    "/projects/{project_id}/simulations",
    response_model=list[StudySummaryResponse],
    status_code=status.HTTP_200_OK,
)
async def list_simulations(
    project_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: SimulationService = Depends(get_simulation_service),
) -> list[StudySummaryResponse]:
    """List a project's studies, newest first."""
    return await service.list_for_project(user, project_id)


@router.get("/simulations/{study_id}", response_model=StudyResponse, status_code=status.HTTP_200_OK)
async def read_simulation(
    study_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: SimulationService = Depends(get_simulation_service),
) -> StudyResponse:
    """Return a study with live job progress."""
    return await service.get(user, study_id)


@router.post(
    "/simulations/{study_id}/cancel", response_model=StudyResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def cancel_simulation(
    study_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: SimulationService = Depends(get_simulation_service),
) -> StudyResponse:
    """Cancel a whole study."""
    return await service.cancel(user, study_id)
