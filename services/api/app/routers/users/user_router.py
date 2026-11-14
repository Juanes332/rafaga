"""HTTP layer of the users domain (architect only)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.models.users.user_schemas import UserCreateRequest, UserResponse
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.security.roles.role_guard import require_architect
from app.services.users.user_service import UserService, get_user_service

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
    dependencies=[
        Depends(require_current_user),
        Depends(enforce_principal_rate_limit),
        Depends(require_architect),
    ],
)


@router.get("", response_model=list[UserResponse], status_code=status.HTTP_200_OK)
async def list_users(service: UserService = Depends(get_user_service)) -> list[UserResponse]:
    """List local users."""
    return await service.list_all()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreateRequest, service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Create a local user."""
    return await service.create(body)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    caller: CurrentUser = Depends(require_current_user),
    service: UserService = Depends(get_user_service),
) -> Response:
    """Delete a user other than the caller."""
    await service.delete(caller, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
