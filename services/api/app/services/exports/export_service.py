"""Exports domain business logic: enqueue PNG renders, read their state."""

import uuid
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.config import Settings, get_settings
from app.core.database.database import get_session
from app.core.errors.result_errors import (
    ExportNotFoundError,
    ExportNotReadyError,
    ResultsIncomparableError,
    ResultsMissingError,
)
from app.models.exports.export_schemas import (
    ExportAcceptedResponse,
    ExportCreateRequest,
    ExportResponse,
)
from app.repositories.comfort import comfort_repository as comfort_repo
from app.repositories.exports import export_repository as repo
from app.repositories.projects.project_repository import find_project
from app.repositories.results.result_repository import find_job_scene
from app.security.jwt.jwt_guard import CurrentUser
from app.services.comfort.comfort_service import ComfortService, get_comfort_service
from app.services.comfort.lawson_service import caller_settings
from app.services.comfort.light_jobs import enqueue_light_job
from app.services.comparisons.comparison_service import differences
from app.services.exports.job_view import DISCLAIMER, job_view, wind_label
from app.services.projects.project_access_service import (
    ProjectAccessService,
    get_project_access_service,
)
from app.services.results.result_service import ResultService, get_result_service


class ExportService:
    """Create PNG export jobs and expose their lifecycle."""

    def __init__(self, session: AsyncSession, access: ProjectAccessService,
                 results: ResultService, comfort: ComfortService, settings: Settings) -> None:
        """Bind collaborators."""
        self._s, self._access, self._results = session, access, results
        self._comfort, self._settings = comfort, settings

    async def _comfort_dir(self, user: CurrentUser, study_id: UUID) -> str:
        """Return the comfort directory for the current Lawson table."""
        study = await self._comfort.study(user, study_id)
        _, _, digest = await self._comfort._current(user, study)
        row = await comfort_repo.find_comfort(self._s, study_id, digest)
        if row is None:
            raise ResultsMissingError()
        return row["dir"]

    async def _compare(self, user: CurrentUser, a: dict, body: ExportCreateRequest) -> dict | None:
        """Load the comparison result and require comparability."""
        if body.compare_result_id is None:
            return None
        b = await self._results.load(user, body.compare_result_id, write=True,
                                     not_found=ResultsMissingError)
        if a["comparability_key"] != b["comparability_key"]:
            raise ResultsIncomparableError(details={"differences": differences(a, b)})
        return b

    async def create(self, user: CurrentUser, body: ExportCreateRequest) -> ExportAcceptedResponse:
        """Enqueue a light-lane render job and record the export."""
        a = await self._results.load(user, body.result_id, write=True, not_found=ResultsMissingError)
        b = await self._compare(user, a, body)
        comfort_dir = await self._comfort_dir(user, a["study_id"]) if body.layer == "lawson" else None
        export_id = uuid.uuid4()
        payload = await self._payload(user, export_id, a, b, comfort_dir, body)
        job_id = await enqueue_light_job(self._s, self._settings, project_id=a["project_id"],
                                         owner_id=user.id, study_id=None, kind="render", payload=payload)
        await repo.insert_export(self._s, export_id=export_id, owner_id=user.id,
                                 project_id=a["project_id"], job_id=job_id, layer=body.layer,
                                 params=body.model_dump(mode="json"))
        await self._s.commit()
        return ExportAcceptedResponse(export_id=export_id)

    async def _payload(self, user: CurrentUser, export_id: UUID, a: dict, b: dict | None,
                       comfort_dir: str | None, body: ExportCreateRequest) -> dict[str, Any]:
        """Build the render payload of job-contract 3.5."""
        project = await find_project(self._s, a["project_id"])
        th = {**(await caller_settings(self._s, user.id))["thresholds"],
              **(body.thresholds.model_dump(exclude_none=True) if body.thresholds else {})}
        return {
            "contract_version": 1, "job_kind": "render", "project_id": str(a["project_id"]),
            "export_id": str(export_id), "output_dir": f"exports/{user.id}",
            "file_name": f"{export_id}.png", "layer": body.layer, "result_dir": a["dir"],
            "compare_result_dir": b["dir"] if b else None, "comfort_dir": comfort_dir,
            "output_grid": a["output_grid"], "thresholds": th, "dpi": body.dpi,
            "labels": {
                "project_name": project["name"],
                "alternative_a": await repo.alternative_name(self._s, a["alternative_id"]),
                "alternative_b": await repo.alternative_name(self._s, b["alternative_id"]) if b else None,
                "wind": wind_label(a["direction_deg"]), "disclaimer": DISCLAIMER},
            "scene": await find_job_scene(self._s, a["job_id"]),
        }

    async def _load(self, user: CurrentUser, export_id: UUID) -> dict[str, Any]:
        """Return the export row after the ownership check."""
        row = await repo.find_export(self._s, export_id)
        pid = row["project_id"] if row else UUID(int=0)
        await self._access.resolve(pid, user, not_found=ExportNotFoundError)
        return dict(row)

    async def get(self, user: CurrentUser, export_id: UUID) -> ExportResponse:
        """Return the export status."""
        row = await self._load(user, export_id)
        return ExportResponse(id=row["id"], file_ready=row["file"] is not None, **job_view(row))

    async def file(self, user: CurrentUser, export_id: UUID) -> Path:
        """Return the PNG path, or 409 while it is not rendered."""
        row = await self._load(user, export_id)
        path = (Path(self._settings.data_dir) / (row["file"] or "")).resolve()
        if not row["file"] or not path.is_file():
            raise ExportNotReadyError()
        return path


def get_export_service(
    session: AsyncSession = Depends(get_session),
    access: ProjectAccessService = Depends(get_project_access_service),
    results: ResultService = Depends(get_result_service),
    comfort: ComfortService = Depends(get_comfort_service),
    settings: Settings = Depends(get_settings),
) -> ExportService:
    """Provide the export service for a request."""
    return ExportService(session, access, results, comfort, settings)
