"""GET /health: the only HTTP route of the solver (SOL-01)."""

from fastapi import APIRouter, Request, Response, status
from fastapi.concurrency import run_in_threadpool

from app.models.health.health_schemas import HealthResponse
from app.services.health.health_service import HealthService

router = APIRouter(tags=["health"])


def get_health_service(request: Request) -> HealthService:
    """Return the app-owned health service."""
    return request.app.state.health_service


@router.get(
    "/health", response_model=HealthResponse, status_code=status.HTTP_200_OK,
    responses={503: {"model": HealthResponse}},
)
async def health(request: Request, response: Response) -> HealthResponse:
    """Return device, DB and lane state; 503 while the DB is unreachable."""
    report = await run_in_threadpool(get_health_service(request).check)
    if report.db != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return report
