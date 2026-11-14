"""HTTP layer of the OSM tile proxy."""

from fastapi import APIRouter, Depends, Response, status

from app.security.jwt.jwt_guard import require_current_user
from app.security.rate_limit.rate_limiter import enforce_tiles_rate_limit
from app.services.tiles.tile_service import TileService, get_tile_service

router = APIRouter(
    prefix="/api/v1/tiles",
    tags=["tiles"],
    dependencies=[Depends(require_current_user), Depends(enforce_tiles_rate_limit)],
)


@router.get(
    "/{z}/{x}/{y}.png",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}},
    status_code=status.HTTP_200_OK,
)
async def read_tile(
    z: int, x: int, y: int, service: TileService = Depends(get_tile_service)
) -> Response:
    """Return a map tile as image/png."""
    data = await service.get(z, x, y)
    return Response(content=data, media_type="image/png",
                    headers={"Cache-Control": "private, max-age=604800"})
