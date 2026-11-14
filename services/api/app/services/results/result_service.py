"""Results domain business logic."""

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any
from uuid import UUID

import numpy as np
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.config import Settings, get_settings
from app.core.database.database import get_session
from app.core.errors.error_contract import AppError
from app.core.errors.result_errors import (
    FieldNotFoundError,
    ImageNotFoundError,
    InvalidThresholdsError,
    ResultNotFoundError,
    ViewerNotAvailableError,
)
from app.models.results.result_schemas import (
    ResultResponse,
    Viewer3DResponse,
    ZoneAreasResponse,
)
from app.repositories.results import result_repository as repo
from app.security.jwt.jwt_guard import CurrentUser
from app.services.comfort.lawson_service import caller_settings
from app.services.projects.project_access_service import (
    ProjectAccessService,
    get_project_access_service,
)
from app.services.results.result_files import (
    entry_by_name, image_file_name, load_field, safe_path, warning_code,
)
from app.services.results.zone_calculator import compute_zones, fluid_area


IMAGE_NAME = re.compile(r"(k|zones|speed|lawson|delta|slice_[a-z0-9_]+)(\.png)?")


class ResultService:
    """Read results and derive zone areas, viewer data and downloads."""

    def __init__(self, session: AsyncSession, access: ProjectAccessService, settings: Settings) -> None:
        """Bind collaborators."""
        self._session, self._access, self._settings = session, access, settings

    async def load(self, user: CurrentUser, result_id: UUID, *, write: bool = False,
                   not_found: Callable[[], AppError] = ResultNotFoundError) -> dict[str, Any]:
        """Return the result row after proving the caller may use it."""
        row = await repo.find_result(self._session, result_id)
        pid = row["project_id"] if row else UUID(int=0)
        await self._access.resolve(pid, user, write=write, not_found=not_found)
        return dict(row)

    async def get(self, user: CurrentUser, result_id: UUID) -> ResultResponse:
        """Return the Result schema."""
        row = await self.load(user, result_id)
        conv = {**row["convergence"], "flow_throughs": row["convergence"].get("averaged_ft"),
                "rel_change": row["convergence"].get("rel_change_last")}
        return ResultResponse(
            **{k: row[k] for k in ("id", "job_id", "study_id", "kind", "direction_deg", "device",
                                   "dx_m", "output_grid", "stats", "comparability_key",
                                   "created_at")},
            convergence=conv, fields=[f["name"] for f in row["fields"]],
            images=[image_file_name(i) for i in row["images"]],
            warnings=[warning_code(w) for w in row["warnings"]])

    async def field_file(self, user: CurrentUser, result_id: UUID, name: str) -> tuple[Path, dict]:
        """Return the path and entry of an allow-listed field."""
        row = await self.load(user, result_id)
        entry = entry_by_name(row["fields"], name)
        path = safe_path(self._settings, row, entry["file"]) if entry else None
        if entry is None or path is None:
            raise FieldNotFoundError()
        return path, entry

    async def image_file(self, user: CurrentUser, result_id: UUID, name: str) -> Path:
        """Return the path of an allow-listed preview image."""
        row = await self.load(user, result_id)
        if not IMAGE_NAME.fullmatch(name):
            raise ImageNotFoundError()
        entry = entry_by_name(row["images"], name.removesuffix(".png"))
        path = safe_path(self._settings, row, entry["file"]) if entry else None
        if path is None:
            raise ImageNotFoundError()
        return path

    async def zones(self, user: CurrentUser, result_id: UUID, k_accel: float | None,
                    k_stagnation: float | None) -> ZoneAreasResponse:
        """Compute acceleration and stagnation areas for the thresholds."""
        row = await self.load(user, result_id)
        defaults = (await caller_settings(self._session, user.id))["thresholds"]
        ka, ks = k_accel or defaults["k_accel"], k_stagnation or defaults["k_stagnation"]
        if ka <= 0 or ks <= 0 or ka <= ks:
            raise InvalidThresholdsError()
        k = load_field(self._settings, row, "K")
        if k is None:
            raise FieldNotFoundError()
        return ZoneAreasResponse(
            result_id=row["id"], thresholds={"k_accel": ka, "k_stagnation": ks},
            fluid_area_m2=fluid_area(k, row["dx_m"]), zones=compute_zones(k, row["dx_m"], ka, ks))

    async def viewer3d(self, user: CurrentUser, result_id: UUID) -> Viewer3DResponse:
        """Return the 3D viewer manifest of a volume result."""
        row = await self.load(user, result_id)
        path = safe_path(self._settings, row, "volume/viewer3d.json")
        if row["kind"] != "volume3d" or path is None:
            raise ViewerNotAvailableError()
        viewer = json.loads(path.read_text())
        scene = await repo.find_job_scene(self._session, row["job_id"])
        return Viewer3DResponse(scene=scene, slices=viewer.get("slices", []),
                                streamlines=viewer.get("streamlines", []))

    async def npz_path(self, user: CurrentUser, result_id: UUID) -> Path:
        """Return the fields.npz bundle path."""
        row = await self.load(user, result_id)
        path = safe_path(self._settings, row, "fields.npz")
        if path is None:
            raise FieldNotFoundError()
        return path

    async def csv_text(self, user: CurrentUser, result_id: UUID) -> str:
        """Render x,y,K,ux,uy,speed rows for the fluid cells."""
        row = await self.load(user, result_id)
        arrays = {n: load_field(self._settings, row, n) for n in ("K", "ux", "uy", "speed")}
        if any(a is None for a in arrays.values()):
            raise FieldNotFoundError()
        g, dx = row["output_grid"], row["dx_m"]
        jj, ii = np.nonzero(np.isfinite(arrays["K"]))
        lines = ["x,y,K,ux,uy,speed"]
        for j, i in zip(jj.tolist(), ii.tolist()):
            vals = ",".join(repr(float(arrays[n][j, i])) for n in ("K", "ux", "uy", "speed"))
            lines.append(f"{g['origin_x'] + (i + 0.5) * dx!r},{g['origin_y'] + (j + 0.5) * dx!r},{vals}")
        return "\n".join(lines) + "\n"


def get_result_service(
    session: AsyncSession = Depends(get_session),
    access: ProjectAccessService = Depends(get_project_access_service),
    settings: Settings = Depends(get_settings),
) -> ResultService:
    """Provide the result service for a request."""
    return ResultService(session, access, settings)
