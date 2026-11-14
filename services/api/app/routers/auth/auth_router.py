"""HTTP layer of the auth domain: public setup/login, guarded /me."""

from fastapi import APIRouter, Depends, status

from app.models.auth.auth_schemas import (
    CredentialsRequest,
    LoginRequest,
    SetupStatusResponse,
    TokenResponse,
)
from app.models.users.user_schemas import UserResponse
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import (
    enforce_login_rate_limit,
    enforce_principal_rate_limit,
)
from app.services.auth.auth_service import AuthService, get_auth_service

public_router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@public_router.get(
    "/setup-status", response_model=SetupStatusResponse, status_code=status.HTTP_200_OK
)
async def read_setup_status(
    service: AuthService = Depends(get_auth_service),
) -> SetupStatusResponse:
    """Tell the SPA whether to show the first-run screen."""
    return SetupStatusResponse(needs_setup=await service.needs_setup())


@public_router.post(
    "/setup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_login_rate_limit)],
)
async def setup_first_user(
    body: CredentialsRequest, service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Create the first architect while the users table is empty."""
    return await service.setup(body.email, body.password)


@public_router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(enforce_login_rate_limit)],
)
async def login(
    body: LoginRequest, service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Exchange credentials for a bearer token."""
    return await service.login(body.email, body.password)


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def read_me(user: CurrentUser = Depends(require_current_user)) -> UserResponse:
    """Return the identity behind the bearer token."""
    return UserResponse(id=user.id, email=user.email, role=user.role)
