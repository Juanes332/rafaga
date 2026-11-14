"""HTTP layer of the geo domain."""

from fastapi import APIRouter, Depends, Query, status

from app.models.geo.geo_schemas import ElevationResponse, GeoResult, TerrainCategory
from app.security.jwt.jwt_guard import require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.geo.geo_service import GeoService, get_geo_service, terrain_categories

router = APIRouter(
    prefix="/api/v1",
    tags=["geo"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.get("/geo/search", response_model=list[GeoResult], status_code=status.HTTP_200_OK)
async def search_places(
    q: str = Query(min_length=2, max_length=100),
    service: GeoService = Depends(get_geo_service),
) -> list[GeoResult]:
    """Geocode a place name through Open-Meteo."""
    return await service.search(q)


@router.get("/geo/elevation", response_model=ElevationResponse, status_code=status.HTTP_200_OK)
async def read_elevation(
    lat: float, lon: float, service: GeoService = Depends(get_geo_service)
) -> ElevationResponse:
    """Return elevation and ISA density for coordinates."""
    return await service.elevation(lat, lon)


@router.get(
    "/terrain-categories", response_model=list[TerrainCategory], status_code=status.HTTP_200_OK
)
async def list_terrain_categories() -> list[TerrainCategory]:
    """Return the five BR-08 terrain categories."""
    return terrain_categories()
