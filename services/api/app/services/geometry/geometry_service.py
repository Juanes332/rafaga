"""Geometry domain business logic for the base case."""

from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_session
from app.core.errors.geometry_errors import BaseLockedError, VersionConflictError
from app.models.geometry.geometry_schemas import (
    Building,
    GeometryPutRequest,
    GeometryResponse,
    GeometryValidationResponse,
)
from app.repositories.geometry import geometry_repository as repo
from app.security.jwt.jwt_guard import CurrentUser
from app.services.geometry.geometry_validation_service import validate_buildings
from app.services.projects.project_access_service import (
    ProjectAccessService,
    get_project_access_service,
)


class GeometryService:
    """Read, validate and replace a project's building set."""

    def __init__(self, session: AsyncSession, access: ProjectAccessService) -> None:
        """Bind collaborators."""
        self._session = session
        self._access = access

    async def snapshot(
        self, project_id: UUID, orphaned: list[UUID] | None = None
    ) -> GeometryResponse:
        """Load the stored geometry and attach its issues."""
        row = await repo.get_geometry(self._session, project_id)
        buildings = [Building(**b) for b in row["buildings"]]
        return GeometryResponse(
            version=row["version"], buildings=buildings,
            issues=validate_buildings(buildings), orphaned_elements=orphaned or [],
        )

    async def get(self, user: CurrentUser, project_id: UUID) -> GeometryResponse:
        """Return the stored geometry with its issues."""
        await self._access.resolve(project_id, user)
        return await self.snapshot(project_id)

    async def validate(
        self, user: CurrentUser, project_id: UUID, buildings: list[Building] | None
    ) -> GeometryValidationResponse:
        """Validate submitted or stored buildings without saving."""
        await self._access.resolve(project_id, user)
        if buildings is None:
            buildings = (await self.snapshot(project_id)).buildings
        return GeometryValidationResponse(issues=validate_buildings(buildings))

    async def ensure_base_unlocked(self, project_id: UUID, confirmed: bool) -> None:
        """Raise BaseLockedError when alternatives exist and no confirmation."""
        if not confirmed and await repo.count_non_base_alternatives(self._session, project_id):
            raise BaseLockedError()

    async def store(
        self, project_id: UUID, expected: int, buildings: list[Building]
    ) -> list[UUID]:
        """Store a building set atomically and return orphaned element ids."""
        new_version = await repo.replace_if_version(
            self._session, project_id, expected, [b.to_json() for b in buildings]
        )
        if new_version is None:
            raise VersionConflictError()
        edges = {b.id: len(b.footprint) for b in buildings}
        refs = await repo.element_refs(self._session, project_id)
        return [i for i, bid, edge in refs if edge >= edges.get(bid, 0)]

    async def put(
        self, user: CurrentUser, project_id: UUID, body: GeometryPutRequest
    ) -> GeometryResponse:
        """Replace the building set under optimistic locking (BR-09)."""
        await self._access.resolve(project_id, user, write=True)
        await self.ensure_base_unlocked(project_id, body.confirm_base_change)
        orphaned = await self.store(project_id, body.expected_version, body.buildings)
        await self._session.commit()
        return await self.snapshot(project_id, orphaned)


def get_geometry_service(
    session: AsyncSession = Depends(get_session),
    access: ProjectAccessService = Depends(get_project_access_service),
) -> GeometryService:
    """Provide the geometry service for a request."""
    return GeometryService(session, access)
