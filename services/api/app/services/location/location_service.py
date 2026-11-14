"""Location domain: place a project and derive elevation and density."""

from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import get_session
from app.models.location.location_schemas import LocationRequest
from app.models.projects.project_schemas import ProjectResponse
from app.repositories.projects import project_repository as projects
from app.security.jwt.jwt_guard import CurrentUser
from app.services.geo.geo_service import GeoService, check_coordinates, get_geo_service
from app.services.geo.isa_density import isa_density
from app.services.projects.project_access_service import (
    ProjectAccessService,
    get_project_access_service,
)
from app.services.projects.project_service import to_response


class LocationService:
    """Set a project's coordinates, elevation and ISA density."""

    def __init__(self, session: AsyncSession, access: ProjectAccessService, geo: GeoService) -> None:
        """Bind collaborators."""
        self._session, self._access, self._geo = session, access, geo

    async def set_location(
        self, user: CurrentUser, project_id: UUID, body: LocationRequest
    ) -> ProjectResponse:
        """Store coordinates (5 decimals) and elevation with its source."""
        await self._access.resolve(project_id, user, write=True)
        check_coordinates(body.lat, body.lon)
        manual = body.elevation_m is not None
        height = body.elevation_m if manual else await self._geo.elevation_m(body.lat, body.lon)
        row = await projects.update_project(self._session, project_id, {
            "lat": round(body.lat, 5), "lon": round(body.lon, 5), "elevation_m": height,
            "elevation_source": "manual" if manual else "open_meteo",
            "air_density_kg_m3": isa_density(height)})
        await self._session.commit()
        return to_response(row, "owner")


def get_location_service(
    session: AsyncSession = Depends(get_session),
    access: ProjectAccessService = Depends(get_project_access_service),
    geo: GeoService = Depends(get_geo_service),
) -> LocationService:
    """Provide the location service for a request."""
    return LocationService(session, access, geo)
