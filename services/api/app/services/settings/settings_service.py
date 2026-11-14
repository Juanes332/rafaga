"""Settings domain business logic: lazy defaults and validated patches."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.config import Settings, get_settings
from app.core.database.database import get_session
from app.models.settings.settings_schemas import (
    LawsonTable,
    SettingsPatchRequest,
    SettingsResponse,
    Thresholds,
)
from app.repositories.settings import settings_repository as repo
from app.security.jwt.jwt_guard import CurrentUser

DEFAULT_TURBULENCE = 0.25
DEFAULT_VEGETATION_CD = 0.2


def _to_response(row: Mapping[str, Any]) -> SettingsResponse:
    """Build the response model from a stored row."""
    return SettingsResponse(
        thresholds=Thresholds(**row["thresholds"]),
        lawson=LawsonTable(**row["lawson"]),
        turbulence_intensity_default=row["turbulence_intensity_default"],
        vegetation_cd=row["vegetation_cd"],
        alternatives_limit=row["alternatives_limit"],
    )


class SettingsService:
    """Read and update the caller's settings."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        """Bind collaborators."""
        self._session = session
        self._settings = settings

    def _defaults(self) -> dict[str, Any]:
        """Return the documented defaults as storable data."""
        return {
            "thresholds": Thresholds().model_dump(),
            "lawson": LawsonTable().model_dump(),
            "turbulence_intensity_default": DEFAULT_TURBULENCE,
            "vegetation_cd": DEFAULT_VEGETATION_CD,
            "alternatives_limit": self._settings.alternatives_limit_default,
        }

    async def get_for(self, user_id: UUID) -> SettingsResponse:
        """Return the settings, creating the row on first access."""
        row = await repo.find_settings(self._session, user_id)
        if row is None:
            row = await repo.upsert_settings(self._session, user_id, self._defaults())
            await self._session.commit()
        return _to_response(row)

    async def patch(self, user: CurrentUser, body: SettingsPatchRequest) -> SettingsResponse:
        """Merge the provided fields over the stored settings."""
        current = (await self.get_for(user.id)).model_dump()
        current.update(body.model_dump(exclude_none=True))
        row = await repo.upsert_settings(self._session, user.id, current)
        await self._session.commit()
        return _to_response(row)


def get_settings_service(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> SettingsService:
    """Provide the settings service for a request."""
    return SettingsService(session, settings)
