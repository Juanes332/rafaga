"""Reports domain business logic."""

import re
import unicodedata
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.config import Settings, get_settings
from app.core.database.database import get_session
from app.core.errors.result_errors import (
    ReportNotFoundError,
    ReportNotReadyError,
    ResultsMissingError,
)
from app.models.exports.export_schemas import (
    ReportAcceptedResponse,
    ReportCreateRequest,
    ReportResponse,
)
from app.repositories.comfort.comfort_repository import find_study
from app.repositories.projects.project_repository import find_project
from app.repositories.reports import report_repository as repo
from app.security.jwt.jwt_guard import CurrentUser
from app.services.comfort.lawson_service import caller_settings
from app.services.simulations.aggregate_template import lawson_block
from app.services.comfort.light_jobs import enqueue_light_job
from app.services.exports.job_view import DISCLAIMER, job_view
from app.services.projects.project_access_service import (
    ProjectAccessService,
    get_project_access_service,
)
from app.services.reports.report_snapshot import study_snapshot


def slugify(name: str) -> str:
    """Return an ASCII slug of a project name."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-") or "proyecto"


def _response(row: Any) -> ReportResponse:
    """Map a joined report row to the Report schema."""
    return ReportResponse(id=row["id"], version=row["version"], created_at=row["created_at"],
                          **job_view(row))


class ReportService:
    """Enqueue PDF report jobs and expose their lifecycle."""

    def __init__(self, session: AsyncSession, access: ProjectAccessService, settings: Settings) -> None:
        """Bind collaborators."""
        self._s, self._access, self._settings = session, access, settings

    async def _studies(self, project_id: UUID, body: ReportCreateRequest, cfg: dict) -> list[dict]:
        """Return snapshots of the requested studies of this project."""
        out = []
        for sid in body.study_ids:
            study = await find_study(self._s, sid)
            if study is None or study["project_id"] != project_id:
                raise ResultsMissingError()
            snap = await study_snapshot(self._s, self._settings, dict(study), cfg, body.include_comfort)
            if snap is not None:
                out.append(snap)
        if not out:
            raise ResultsMissingError()
        return out

    async def _snapshot(self, project: Any, studies: list[dict], cfg: dict,
                        baseline: UUID | None) -> dict[str, Any]:
        """Assemble the report snapshot."""
        wind = await repo.wind_row(self._s, project["id"])
        keys = ("name", "lat", "lon", "elevation_m", "elevation_source", "air_density_kg_m3",
                "analysis_height_m")
        return {
            "project": {k: project[k] for k in keys},
            "wind": {"source": wind["source"], "period_years": wind["period_years"],
                     "terrain_category": wind["terrain_category"], "z0_m": wind["z0_m"],
                     "rose": wind["rose"]},
            "studies": studies, "baseline_study_id": str(baseline) if baseline else None,
            "thresholds": cfg["thresholds"], "lawson": lawson_block(cfg["lawson"]),
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "app_version": self._settings.app_version, "disclaimer": DISCLAIMER,
        }

    async def create(self, user: CurrentUser, project_id: UUID,
                     body: ReportCreateRequest) -> ReportAcceptedResponse:
        """Snapshot the studies and enqueue the report job."""
        await self._access.resolve(project_id, user, write=True)
        project = await find_project(self._s, project_id)
        cfg = await caller_settings(self._s, user.id)
        studies = await self._studies(project_id, body, cfg)
        version = await repo.next_version(self._s, project_id)
        report_id, file_name = uuid.uuid4(), f"rafaga-{slugify(project['name'])}-v{version}.pdf"
        payload = {
            "contract_version": 1, "job_kind": "report", "project_id": str(project_id),
            "report_id": str(report_id), "version": version, "output_dir": f"reports/{project_id}",
            "file_name": file_name,
            "snapshot": await self._snapshot(project, studies, cfg, body.baseline_study_id)}
        job_id = await enqueue_light_job(self._s, self._settings, project_id=project_id,
                                         owner_id=user.id, study_id=None, kind="report", payload=payload)
        params = {**body.model_dump(mode="json"), "file_name": file_name}
        await repo.insert_report(self._s, report_id=report_id, project_id=project_id,
                                 owner_id=user.id, job_id=job_id, version=version, params=params)
        await self._s.commit()
        return ReportAcceptedResponse(report_id=report_id)

    async def list(self, user: CurrentUser, project_id: UUID) -> list[ReportResponse]:
        """List a project's reports."""
        await self._access.resolve(project_id, user)
        return [_response(r) for r in await repo.list_reports(self._s, project_id)]

    async def _load(self, user: CurrentUser, report_id: UUID) -> Any:
        """Return the report row after the ownership check."""
        row = await repo.find_report(self._s, report_id)
        pid = row["project_id"] if row else UUID(int=0)
        await self._access.resolve(pid, user, not_found=ReportNotFoundError)
        return row

    async def get(self, user: CurrentUser, report_id: UUID) -> ReportResponse:
        """Return the report status."""
        return _response(await self._load(user, report_id))

    async def file(self, user: CurrentUser, report_id: UUID) -> tuple[Path, str]:
        """Return the PDF path and download name, or 409 when not ready."""
        row = await self._load(user, report_id)
        path = (Path(self._settings.data_dir) / (row["file"] or "")).resolve()
        if not row["file"] or not path.is_file():
            raise ReportNotReadyError()
        return path, row["params"]["file_name"]


def get_report_service(
    session: AsyncSession = Depends(get_session),
    access: ProjectAccessService = Depends(get_project_access_service),
    settings: Settings = Depends(get_settings),
) -> ReportService:
    """Provide the report service for a request."""
    return ReportService(session, access, settings)
