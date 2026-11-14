"""Scene domain business logic: compile an alternative for the solver."""

from typing import Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.config import Settings, get_settings
from app.core.database.database import get_session
from app.core.errors.alternative_errors import AlternativeNotFoundError, NoBuildingsError
from app.repositories.alternatives.alternative_repository import find_alternative
from app.repositories.scene import scene_repository as repo
from app.security.jwt.jwt_guard import CurrentUser
from app.services.projects.project_access_service import (
    ProjectAccessService,
    get_project_access_service,
)
from app.services.scene.scene_compiler import compile_scene


class SceneService:
    """Compile base geometry plus one alternative's facade elements."""

    def __init__(self, session: AsyncSession, access: ProjectAccessService, settings: Settings) -> None:
        """Bind collaborators."""
        self._session = session
        self._access = access
        self._settings = settings

    async def compile_for_alternative(self, user: CurrentUser, alternative_id: UUID) -> dict[str, Any]:
        """Return the canonical scene of an alternative the caller may read.

        Raises AlternativeNotFoundError for a missing or foreign id and
        NoBuildingsError when the project has no usable building.
        """
        alt = await find_alternative(self._session, alternative_id)
        await self._access.resolve(alt["project_id"] if alt else alternative_id, user,
                                   not_found=AlternativeNotFoundError)
        data = await repo.load_scene_inputs(self._session, alt["project_id"], alternative_id)
        if not data["buildings"]:
            raise NoBuildingsError()
        return compile_scene(
            project_id=str(alt["project_id"]), alternative_id=str(alternative_id),
            geometry_version=data["version"], buildings=data["buildings"],
            elements=data["elements"], z0_m=float(data["z0_m"]),
            analysis_height_m=float(data["analysis_height_m"]),
            vegetation_cd=float(data["cd"]), envelope_m=self._settings.facade_envelope_m,
        )


def get_scene_service(
    session: AsyncSession = Depends(get_session),
    access: ProjectAccessService = Depends(get_project_access_service),
    settings: Settings = Depends(get_settings),
) -> SceneService:
    """Provide the scene service for a request."""
    return SceneService(session, access, settings)
