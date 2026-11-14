"""HTTP layer of the settings domain."""

from fastapi import APIRouter, Depends, status

from app.models.settings.settings_schemas import SettingsPatchRequest, SettingsResponse
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.settings.settings_service import SettingsService, get_settings_service

router = APIRouter(
    prefix="/api/v1/settings",
    tags=["settings"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.get("", response_model=SettingsResponse, status_code=status.HTTP_200_OK)
async def read_settings(
    user: CurrentUser = Depends(require_current_user),
    service: SettingsService = Depends(get_settings_service),
) -> SettingsResponse:
    """Return the caller's settings, defaults on first access."""
    return await service.get_for(user.id)


@router.patch("", response_model=SettingsResponse, status_code=status.HTTP_200_OK)
async def patch_settings(
    body: SettingsPatchRequest,
    user: CurrentUser = Depends(require_current_user),
    service: SettingsService = Depends(get_settings_service),
) -> SettingsResponse:
    """Update thresholds, Lawson table and other preferences."""
    return await service.patch(user, body)
