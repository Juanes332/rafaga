"""HTTP layer for system status."""

from fastapi import APIRouter, Depends, status

from app.models.system.system_schemas import SystemStatusResponse
from app.security.jwt.jwt_guard import require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.system.system_service import SystemService, get_system_service

router = APIRouter(
    prefix="/api/v1/system",
    tags=["system"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.get("/status", response_model=SystemStatusResponse, status_code=status.HTTP_200_OK)
async def read_system_status(
    service: SystemService = Depends(get_system_service),
) -> SystemStatusResponse:
    """Return api/db health and solver capabilities."""
    return await service.status()
