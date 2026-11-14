"""HTTP layer of the templates domain."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.models.templates.template_schemas import (
    ApplyTemplateRequest,
    TemplateCreateRequest,
    TemplateResponse,
    WindClimateResponse,
)
from app.security.jwt.jwt_guard import CurrentUser, require_current_user
from app.security.rate_limit.rate_limiter import enforce_principal_rate_limit
from app.services.templates.template_service import TemplateService, get_template_service

router = APIRouter(
    prefix="/api/v1",
    tags=["templates"],
    dependencies=[Depends(require_current_user), Depends(enforce_principal_rate_limit)],
)


@router.get("/templates", response_model=list[TemplateResponse], status_code=status.HTTP_200_OK)
async def list_templates(
    user: CurrentUser = Depends(require_current_user),
    service: TemplateService = Depends(get_template_service),
) -> list[TemplateResponse]:
    """List the caller's templates."""
    return await service.list_for(user)


@router.post("/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    body: TemplateCreateRequest,
    user: CurrentUser = Depends(require_current_user),
    service: TemplateService = Depends(get_template_service),
) -> TemplateResponse:
    """Save a location-free template."""
    return await service.create(user, body.name, body.payload)


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    user: CurrentUser = Depends(require_current_user),
    service: TemplateService = Depends(get_template_service),
) -> Response:
    """Delete an owned template."""
    await service.delete(user, template_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/projects/{project_id}/apply-template",
    response_model=WindClimateResponse,
    status_code=status.HTTP_200_OK,
)
async def apply_template(
    project_id: UUID,
    body: ApplyTemplateRequest,
    user: CurrentUser = Depends(require_current_user),
    service: TemplateService = Depends(get_template_service),
) -> WindClimateResponse:
    """Apply roughness and thresholds without touching the location."""
    return WindClimateResponse(**await service.apply(user, project_id, body.template_id))
