"""Unauthenticated liveness probe, exempt from both rate-limit tiers."""

from fastapi import APIRouter, Depends, Response, status

from app.models.system.system_schemas import HealthResponse
from app.services.system.system_service import SystemService, get_system_service

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check(
    response: Response, service: SystemService = Depends(get_system_service)
) -> HealthResponse:
    """Return 200 when Postgres answers, 503 degraded otherwise."""
    body = await service.health()
    if body.status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return body
