"""Simulations domain business logic: estimate, create, read, cancel."""

import json
import uuid
from collections.abc import Mapping
from typing import Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.config import Settings, get_settings
from app.core.database.database import get_session
from app.core.errors.simulation_errors import (
    AlternativeNotFoundForRunError,
    BuildingsTooSmallError,
    MeshTooLargeError,
    PayloadTooLargeError,
    StudyNotFoundError,
)
from app.models.simulations.simulation_schemas import (
    EstimateRequest,
    EstimateResponse,
    SimulationCreateRequest,
    StudyResponse,
    StudySummaryResponse,
)
from app.repositories.simulations import study_repository as repo
from app.security.jwt.jwt_guard import CurrentUser
from app.services.projects.project_access_service import (
    ProjectAccessService,
    get_project_access_service,
)
from app.services.settings.settings_service import SettingsService, get_settings_service
from app.services.simulations import aggregate_template, estimate_calculator as ec
from app.services.simulations import grid_service as grids
from app.services.simulations import simulation_constants as c
from app.services.simulations.geometry_check import ensure_simulable
from app.services.simulations.payload_builder import JobContext, build_heavy_payload
from app.services.simulations.scene_port import get_scene_service
from app.services.simulations.simulation_inputs import (
    ensure_located,
    resolve_directions,
    resolve_u10,
)
from app.services.simulations.study_view import study_to_response, study_to_summary


def grid_builder(body: EstimateRequest, scene: Mapping[str, Any], dirs: list[float]):  # noqa: ANN201
    """Return a dx -> [(sim, output)] function for the request."""
    def build(dx: float) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        if body.kind == "section2d":
            s = body.section
            return [grids.section_grids(scene, s.p0, s.p1, dx)]
        out = grids.output_grid_plan(scene, dx)
        return [(grids.sim_grid_wind(scene, d, dx, body.kind == "volume3d"), out) for d in dirs]
    return build


class SimulationService:
    """Plan, queue and read simulation studies."""

    def __init__(self, session: AsyncSession, access: ProjectAccessService,
                 settings: Settings, user_settings: SettingsService, scenes: Any) -> None:
        """Bind collaborators."""
        self._s, self._access, self._cfg = session, access, settings
        self._user_settings, self._scenes = user_settings, scenes

    async def _prepare(self, user: CurrentUser, body: EstimateRequest, write: bool):  # noqa: ANN202
        """Resolve access, inputs, scene and estimate for a request."""
        alt = await repo.find_alternative(self._s, body.alternative_id)
        project_id = alt["project_id"] if alt else uuid.UUID(int=0)
        await self._access.resolve(
            project_id, user, write=write, not_found=AlternativeNotFoundForRunError)
        inputs = await repo.load_inputs(self._s, project_id)
        ensure_located(inputs)
        scene = await self._scenes.compile_for_alternative(user, body.alternative_id)
        ensure_simulable(inputs["buildings"])
        return alt, inputs, scene

    async def _estimate(self, body, scene, dirs):  # noqa: ANN001, ANN202
        """Run the calculator against the latest solver node."""
        node = await repo.latest_solver_node(self._s)
        return ec.compute_estimate(body.kind, scene, body.dx_m, body.device, node,
                                   self._cfg.cpu_max_nodes_3d, grid_builder(body, scene, dirs))

    async def estimate(self, user: CurrentUser, body: EstimateRequest) -> EstimateResponse:
        """Return the memory estimate without creating anything."""
        _, inputs, scene = await self._prepare(user, body, write=False)
        dirs = [] if body.kind == "section2d" else (
            body.directions_deg or [inputs["manual_direction_deg"] or 0.0])
        est = await self._estimate(body, scene, dirs or [0.0])
        data = {k: getattr(est, k) for k in EstimateResponse.model_fields}
        return EstimateResponse(**data)

    async def create(self, user: CurrentUser, body: SimulationCreateRequest) -> StudyResponse:
        """Create a study and one queued heavy job per direction."""
        alt, inputs, scene = await self._prepare(user, body, write=True)
        dirs = resolve_directions(inputs, body)
        u10 = resolve_u10(inputs, c.U10_NOMINAL)
        est = await self._estimate(body, scene, dirs or [0.0])
        self._check_fit(est, body)
        study_id = await self._persist(user, body, alt, inputs, scene, dirs, u10, est)
        await self._s.commit()
        return await self._study_response(await repo.find_study(self._s, study_id))

    def _check_fit(self, est: ec.Estimate, body: SimulationCreateRequest) -> None:
        """Apply the mesh rules; an offline solver defers to its own check."""
        if est.rejected_reason == "buildings_too_small":
            raise BuildingsTooSmallError()
        if est.fits or est.rejected_reason in ("solver_offline", "device_unavailable"):
            return
        if est.proposed_dx_m is None or not body.auto_coarsen:
            raise MeshTooLargeError(details={"proposed_dx_m": est.proposed_dx_m,
                                             "memory_bytes": est.memory_bytes,
                                             "budget_bytes": est.budget_bytes})

    async def _persist(self, user, body, alt, inputs, scene, dirs, u10, est) -> UUID:  # noqa: ANN001
        """Insert the study and its jobs in the caller's transaction."""
        dx = est.dx_used if (body.auto_coarsen and not est.fits and est.proposed_dx_m) else body.dx_m
        build = grid_builder(body, scene, dirs)
        settings = (await self._user_settings.get_for(user.id)).model_dump()
        study_id, pid = uuid.uuid4(), alt["project_id"]
        final = build(dx)
        template = aggregate_template.build_template(inputs, settings, study_id, final[0][1])
        await repo.insert_study(self._s, {
            "id": study_id, "project_id": pid, "alternative_id": alt["id"], "owner_id": user.id,
            "kind": body.kind, "request": json.loads(body.model_dump_json()), "dx_m": dx,
            "auto_coarsened": dx != body.dx_m, "aggregate_template": template})
        for (sim, out), phi in zip(final, dirs or [None], strict=True):
            await self._insert_job(user, body, alt, inputs, scene, settings, study_id, sim, out, phi, u10)
        return study_id

    async def _insert_job(self, user, body, alt, inputs, scene, settings, study_id, sim, out, phi, u10) -> None:  # noqa: ANN001
        """Build one payload, enforce the size limit and insert the job."""
        job_id = uuid.uuid4()
        mem = grids.node_count(sim) * c.BYTES_PER_NODE[body.kind] + c.OVERHEAD_BYTES
        section = body.section.model_dump() if body.section else None
        ctx = JobContext(body.kind, alt["project_id"], study_id, job_id, alt["id"], scene, section,
                         sim["wind_from_deg"], u10, inputs, sim, out, body.device, mem,
                         settings["thresholds"])
        payload = build_heavy_payload(ctx)
        if len(json.dumps(payload, default=str)) > self._cfg.max_payload_mb * 1024 * 1024:
            raise PayloadTooLargeError()
        await repo.insert_job(self._s, {
            "id": job_id, "study_id": study_id, "project_id": alt["project_id"],
            "owner_id": user.id, "kind": body.kind, "direction_deg": phi,
            "payload": json.loads(json.dumps(payload, default=str)), "device": body.device})

    async def _study_response(self, study: Mapping[str, Any]) -> StudyResponse:
        """Return a study with its heavy jobs."""
        jobs = await repo.heavy_jobs_of(self._s, [study["id"]])
        return study_to_response(study, jobs)

    async def _visible_study(self, user: CurrentUser, study_id: UUID, write: bool) -> Mapping[str, Any]:
        """Return a study the caller may see, else the opaque 404."""
        study = await repo.find_study(self._s, study_id)
        pid = study["project_id"] if study else uuid.UUID(int=0)
        await self._access.resolve(pid, user, write=write, not_found=StudyNotFoundError)
        return study

    async def get(self, user: CurrentUser, study_id: UUID) -> StudyResponse:
        """Return one study with live job progress."""
        return await self._study_response(await self._visible_study(user, study_id, False))

    async def list_for_project(self, user: CurrentUser, project_id: UUID) -> list[StudySummaryResponse]:
        """List a project's studies, newest first."""
        await self._access.resolve(project_id, user)
        studies = await repo.list_studies(self._s, project_id)
        jobs = await repo.heavy_jobs_of(self._s, [s["id"] for s in studies])
        return [study_to_summary(s, [j for j in jobs if j["study_id"] == s["id"]]) for s in studies]

    async def cancel(self, user: CurrentUser, study_id: UUID) -> StudyResponse:
        """Cancel queued jobs now and request cancellation of running ones."""
        study = await self._visible_study(user, study_id, True)
        await repo.cancel_study_jobs(self._s, study_id)
        await self._s.commit()
        return await self._study_response(study)


def get_simulation_service(
    session: AsyncSession = Depends(get_session),
    access: ProjectAccessService = Depends(get_project_access_service),
    settings: Settings = Depends(get_settings),
    user_settings: SettingsService = Depends(get_settings_service),
    scenes: Any = Depends(get_scene_service),
) -> SimulationService:
    """Provide the simulation service for a request."""
    return SimulationService(session, access, settings, user_settings, scenes)
