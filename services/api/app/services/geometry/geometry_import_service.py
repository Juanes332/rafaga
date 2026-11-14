"""Import a CAD or mesh file into the base geometry."""

import asyncio
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.config import Settings, get_settings
from app.core.database.database import get_session
from app.core.errors.geometry_errors import ImportFailedError, UnsupportedFormatError
from app.models.geometry.geometry_schemas import Building, ImportReportResponse
from app.repositories.geometry import geometry_repository as repo
from app.security.jwt.jwt_guard import CurrentUser
from app.services.geometry.geometry_service import GeometryService, get_geometry_service
from app.services.geometry.importers.dxf_importer import read_dxf
from app.services.geometry.importers.ifc_importer import read_ifc
from app.services.geometry.importers.importer_common import (
    UNIT_FACTORS,
    ImporterError,
    ImportResult,
    bounds_center,
    scale_building,
    translate_building,
)
from app.services.geometry.importers.mesh_importer import read_mesh
from app.services.projects.project_access_service import (
    ProjectAccessService,
    get_project_access_service,
)
from app.services.uploads.upload_service import read_limited, store_upload

FORMATS = {".dxf", ".stl", ".obj", ".ifc"}


def _parse(data: bytes, extension: str, stem: str) -> ImportResult:
    """Dispatch to the importer of the file extension."""
    if extension == ".dxf":
        return read_dxf(data)
    if extension == ".ifc":
        return read_ifc(data)
    return read_mesh(data, extension.lstrip("."), stem)


def _normalize(result: ImportResult, unit: str, center: bool) -> None:
    """Convert to metres and optionally centre the set on the origin."""
    if not result.metric:
        chosen = unit if unit != "auto" else result.detected_unit
        if chosen not in UNIT_FACTORS:
            result.warnings.append("unit_unknown_assumed_m")
            chosen = "m"
        for b in result.buildings:
            scale_building(b, UNIT_FACTORS[chosen])
    if center and result.buildings:
        cx, cy = bounds_center(result.buildings)
        for b in result.buildings:
            translate_building(b, -cx, -cy)


class GeometryImportService:
    """Parse an uploaded file and merge it into the building set."""

    def __init__(
        self, session: AsyncSession, access: ProjectAccessService,
        geometry: GeometryService, settings: Settings,
    ) -> None:
        """Bind collaborators."""
        self._session, self._access = session, access
        self._geometry, self._settings = geometry, settings

    async def _read(self, file: UploadFile, declared: int) -> tuple[bytes, str]:
        """Return the file bytes and its supported extension."""
        extension = Path(file.filename or "").suffix.lower()
        if extension not in FORMATS:
            raise UnsupportedFormatError(
                details={"supported": sorted(f.lstrip(".") for f in FORMATS)},
                hint="Use DXF, STL, OBJ or IFC.",
            )
        data = await read_limited(file, self._settings.max_geometry_upload_mb, declared)
        return data, extension

    async def import_file(
        self, user: CurrentUser, project_id: UUID, file: UploadFile,
        declared: int, unit: str, mode: str, center: bool,
    ) -> ImportReportResponse:
        """Import the file; any failure leaves the project unchanged."""
        await self._access.resolve(project_id, user, write=True)
        await self._geometry.ensure_base_unlocked(project_id, False)
        data, extension = await self._read(file, declared)
        stem = Path(file.filename or "model").stem
        try:
            result = await asyncio.to_thread(_parse, data, extension, stem)
        except ImporterError as exc:
            raise ImportFailedError(
                exc.cause, details={"cause": exc.cause}, hint=exc.hint) from exc
        _normalize(result, unit, center)
        added = [Building(**b) for b in result.buildings]
        await self._merge(project_id, added, mode)
        await store_upload(self._session, self._settings, project_id, "geometry",
                           file.filename or "upload", data)
        await self._session.commit()
        return await self._report(project_id, result, added)

    async def _merge(self, project_id: UUID, added: list[Building], mode: str) -> None:
        """Append or replace the stored buildings."""
        stored = await repo.get_geometry(self._session, project_id)
        kept = [] if mode == "replace" else [Building(**b) for b in stored["buildings"]]
        await self._geometry.store(project_id, stored["version"], kept + added)

    async def _report(
        self, project_id: UUID, result: ImportResult, added: list[Building]
    ) -> ImportReportResponse:
        """Build the ImportReport with the refreshed geometry."""
        geometry = await self._geometry.snapshot(project_id)
        data: dict[str, Any] = {
            "buildings_added": len(added),
            "missing_height": [b.id for b in added if b.height_m is None],
            "ignored": result.ignored,
            "detected_unit": result.detected_unit if result.metric is False else "m",
            "warnings": result.warnings,
            "geometry": geometry,
        }
        return ImportReportResponse(**data)


def get_geometry_import_service(
    session: AsyncSession = Depends(get_session),
    access: ProjectAccessService = Depends(get_project_access_service),
    geometry: GeometryService = Depends(get_geometry_service),
    settings: Settings = Depends(get_settings),
) -> GeometryImportService:
    """Provide the import service for a request."""
    return GeometryImportService(session, access, geometry, settings)
