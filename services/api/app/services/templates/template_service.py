"""Templates domain business logic."""

from typing import Any
from uuid import UUID

from fastapi import Depends
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_session
from app.core.errors.simulation_errors import (
    TemplateContainsLocationError,
    TemplateInvalidError,
    TemplateNotFoundError,
)
from app.models.settings.settings_schemas import SettingsPatchRequest
from app.models.templates.template_schemas import (
    LOCATION_KEYS,
    TemplatePayload,
    TemplateResponse,
)
from app.repositories.templates import template_repository as repo
from app.security.jwt.jwt_guard import CurrentUser
from app.services.projects.project_access_service import (
    ProjectAccessService,
    get_project_access_service,
)
from app.services.settings.settings_service import SettingsService, get_settings_service
from app.services.templates.wind_response import wind_response


def contains_location_key(value: Any) -> bool:
    """Return whether any dict key at any depth names a location."""
    if isinstance(value, dict):
        return any(
            str(k).lower() in LOCATION_KEYS or contains_location_key(v)
            for k, v in value.items()
        )
    if isinstance(value, list):
        return any(contains_location_key(v) for v in value)
    return False


class TemplateService:
    """Store location-free templates and apply them to projects."""

    def __init__(
        self, session: AsyncSession, access: ProjectAccessService, settings: SettingsService
    ) -> None:
        """Bind collaborators."""
        self._session = session
        self._access = access
        self._settings = settings

    async def list_for(self, user: CurrentUser) -> list[TemplateResponse]:
        """List the caller's templates."""
        rows = await repo.list_templates(self._session, user.id)
        return [TemplateResponse(**r) for r in rows]

    async def create(
        self, user: CurrentUser, name: str, payload: dict[str, Any]
    ) -> TemplateResponse:
        """Validate and store a template, refusing any location key."""
        if contains_location_key(payload):
            raise TemplateContainsLocationError()
        try:
            checked = TemplatePayload(**payload).model_dump(exclude_none=True)
        except ValidationError as exc:
            raise TemplateInvalidError() from exc
        row = await repo.insert_template(self._session, user.id, name, checked)
        await self._session.commit()
        return TemplateResponse(**row)

    async def _owned(self, user: CurrentUser, template_id: UUID) -> dict[str, Any]:
        """Return the template when owned, else the opaque 404."""
        row = await repo.find_template(self._session, template_id)
        if row is None or row["owner_id"] != user.id:
            raise TemplateNotFoundError()
        return dict(row)

    async def delete(self, user: CurrentUser, template_id: UUID) -> None:
        """Delete an owned template."""
        await self._owned(user, template_id)
        await repo.delete_template(self._session, template_id)
        await self._session.commit()

    async def apply(
        self, user: CurrentUser, project_id: UUID, template_id: UUID
    ) -> dict[str, Any]:
        """Apply roughness to the project and thresholds to the caller."""
        await self._access.resolve(project_id, user, write=True)
        payload = (await self._owned(user, template_id))["payload"]
        await repo.apply_roughness(
            self._session, project_id, payload.get("terrain_category"), payload.get("z0_m")
        )
        patch = {k: payload[k] for k in ("thresholds", "lawson") if k in payload}
        try:
            await self._settings.patch(user, SettingsPatchRequest(**patch))
        except ValidationError as exc:
            raise TemplateInvalidError() from exc
        await self._session.commit()
        return wind_response(await repo.find_wind_row(self._session, project_id))


def get_template_service(
    session: AsyncSession = Depends(get_session),
    access: ProjectAccessService = Depends(get_project_access_service),
    settings: SettingsService = Depends(get_settings_service),
) -> TemplateService:
    """Provide the template service for a request."""
    return TemplateService(session, access, settings)
