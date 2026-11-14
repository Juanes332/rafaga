"""Backgrounds domain business logic."""

import asyncio
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.config import Settings, get_settings
from app.core.database.database import get_session
from app.core.errors.geometry_errors import (
    BackgroundNotFoundError,
    PageNotFoundError,
    UnsupportedFormatError,
)
from app.models.backgrounds.background_schemas import (
    BackgroundPatchRequest,
    BackgroundResponse,
)
from app.repositories.backgrounds import background_repository as repo
from app.repositories.uploads.upload_repository import delete_upload
from app.security.jwt.jwt_guard import CurrentUser
from app.services.backgrounds.background_raster import (
    count_pages,
    matches_signature,
    render_page,
)
from app.services.projects.project_access_service import (
    ProjectAccessService,
    get_project_access_service,
)
from app.services.uploads.upload_service import read_limited, remove_file, store_upload

EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf"}


def to_response(row: Mapping[str, Any]) -> BackgroundResponse:
    """Build the BackgroundPlan schema, deriving metres per pixel."""
    cal = row["calibration"]
    mpp = None
    if cal:
        pixels = math.dist(cal["p1"], cal["p2"])
        mpp = cal["distance_m"] / pixels if pixels > 0 else None
    return BackgroundResponse(
        id=row["id"], page_count=row["page_count"], page=row["page"],
        calibration=cal, metres_per_pixel=mpp, transform=row["transform"],
        opacity=row["opacity"],
    )


class BackgroundService:
    """Upload, calibrate, rasterize and delete background plans."""

    def __init__(
        self, session: AsyncSession, access: ProjectAccessService, settings: Settings
    ) -> None:
        """Bind collaborators."""
        self._session, self._access, self._settings = session, access, settings

    async def _plan(
        self, user: CurrentUser, plan_id: UUID, write: bool
    ) -> Mapping[str, Any]:
        """Load a plan after the ownership check; foreign == missing."""
        row = await repo.get_plan(self._session, plan_id)
        if row is None:
            raise BackgroundNotFoundError()
        await self._access.resolve(row["project_id"], user, write=write,
                                   not_found=BackgroundNotFoundError)
        return row

    async def create(
        self, user: CurrentUser, project_id: UUID, file: UploadFile, declared: int
    ) -> BackgroundResponse:
        """Store a PNG/JPG/PDF and create its plan."""
        await self._access.resolve(project_id, user, write=True)
        extension = Path(file.filename or "").suffix.lower()
        if extension not in EXTENSIONS:
            raise UnsupportedFormatError(hint="Use PNG, JPG or PDF.")
        data = await read_limited(file, self._settings.max_image_upload_mb, declared)
        try:
            if not matches_signature(extension, data):
                raise ValueError("signature mismatch")
            pages = await asyncio.to_thread(count_pages, extension, data)
        except ValueError as exc:
            raise UnsupportedFormatError(hint="The file is corrupt or not what its extension says.") from exc
        upload = await store_upload(self._session, self._settings, project_id,
                                    "background", file.filename or "plan", data)
        plan_id = await repo.insert_plan(self._session, project_id, upload, pages)
        await self._session.commit()
        return to_response(await repo.get_plan(self._session, plan_id))

    async def list(self, user: CurrentUser, project_id: UUID) -> list[BackgroundResponse]:
        """List the plans of a project."""
        await self._access.resolve(project_id, user)
        return [to_response(r) for r in await repo.list_plans(self._session, project_id)]

    async def page_png(self, user: CurrentUser, plan_id: UUID, page: int) -> bytes:
        """Return one page of a plan as PNG."""
        row = await self._plan(user, plan_id, False)
        if not 1 <= page <= row["page_count"]:
            raise PageNotFoundError()
        path = Path(self._settings.data_dir) / row["path"]
        return await asyncio.to_thread(render_page, path, page)

    async def patch(
        self, user: CurrentUser, plan_id: UUID, body: BackgroundPatchRequest
    ) -> BackgroundResponse:
        """Store calibration, transform, page or opacity."""
        row = await self._plan(user, plan_id, True)
        fields = body.model_dump(exclude_none=True)
        if "page" in fields and fields["page"] > row["page_count"]:
            raise PageNotFoundError()
        await repo.update_plan(self._session, plan_id, fields)
        await self._session.commit()
        return to_response(await repo.get_plan(self._session, plan_id))

    async def delete(self, user: CurrentUser, plan_id: UUID) -> None:
        """Delete the plan, its upload row and its file."""
        row = await self._plan(user, plan_id, True)
        await delete_upload(self._session, row["upload_id"])
        await self._session.commit()
        remove_file(self._settings, row["path"])


def get_background_service(
    session: AsyncSession = Depends(get_session),
    access: ProjectAccessService = Depends(get_project_access_service),
    settings: Settings = Depends(get_settings),
) -> BackgroundService:
    """Provide the background service for a request."""
    return BackgroundService(session, access, settings)
