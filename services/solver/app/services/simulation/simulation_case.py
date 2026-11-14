"""A heavy job translated into a lattice problem plus its metadata."""

from dataclasses import dataclass, field

import numpy as np

from app.models.jobs.payload_schemas import HeavyPayload
from app.services.lattice.lattice_problem import SOLID, LatticeProblem
from app.services.lattice.lattice_units import (
    RE_SHARP_EDGE,
    LatticeUnits,
    effective_reynolds,
)
from app.services.voxelize.frame_transform import WindFrame


@dataclass
class SimulationCase:
    """Lattice problem with frame, reference speed and convergence window."""

    payload: HeavyPayload
    problem: LatticeProblem
    units: LatticeUnits
    u_ref_lat: float
    frame: WindFrame | None
    window: np.ndarray  # flat node indices sampled by the convergence check
    warnings: list[dict] = field(default_factory=list)

    @property
    def kind(self) -> str:
        """Return the job kind."""
        return self.payload.job_kind


def plan_window(frame: WindFrame, payload: HeavyPayload, mask2d: np.ndarray) -> np.ndarray:
    """Return flat indices of fluid sim cells inside the output rectangle."""
    sim, out = payload.grid.sim, payload.grid.output
    ny, nx = mask2d.shape
    xs = sim.origin[0] + (np.arange(nx) + 0.5) * sim.dx_m
    ys = sim.origin[1] + (np.arange(ny) + 0.5) * sim.dx_m
    gx, gy = np.meshgrid(xs, ys)
    east = gx * frame.d[0] + gy * frame.n[0]
    north = gx * frame.d[1] + gy * frame.n[1]
    inside = (
        (east >= out.origin_x) & (east <= out.origin_x + out.nx * out.dx_m)
        & (north >= out.origin_y) & (north <= out.origin_y + out.ny * out.dx_m)
    )
    return np.flatnonzero((inside & (mask2d != SOLID)).reshape(-1))


def reynolds_warnings(payload: HeavyPayload, units: LatticeUnits) -> list[dict]:
    """Return scene warnings plus low_reynolds below Snyder's sharp-edge limit.

    ADR-14's 2e4 fired on every default mesh (H = 18 cells at dx = 1 m)
    although the floored lattice viscosity is negligible next to the
    turbulence model wherever the flow separates. Sharp-edged blocks are
    Re-independent above Re_H ~ 1.1e4 (Snyder 1981), i.e. H >= 11 cells
    with the floor; only below that is the warning actionable.
    """
    warnings = [w.model_dump() for w in payload.scene.warnings]
    h_cells = payload.scene.h_max_m / payload.grid.sim.dx_m
    if effective_reynolds(units.u_lat, h_cells, units.nu_lat) < RE_SHARP_EDGE:
        warnings.append({"code": "low_reynolds", "ref": payload.scene.source_ref()})
    return warnings


# Elements that only act through 3D mechanisms (deflecting the downwash).
_THREE_D_ONLY = ("canopy",)


def plan_representability_warnings(payload: HeavyPayload) -> list[dict]:
    """Return element_not_representable_2d for facade elements a plan cannot show.

    A plan at z_a sees a prism only if it crosses z_a, and even then a
    canopy works by catching the downwash of the facade above it, which
    a plan has no vertical dimension for. One warning per element id.
    """
    z_a = payload.scene.analysis_height_m
    seen: list[str] = []
    for prim in [*payload.scene.solids, *payload.scene.porous]:
        ref = prim.origin.element_id
        if ref is None or ref in seen:
            continue
        crosses = prim.z_min <= z_a <= prim.z_max
        if prim.origin.kind in _THREE_D_ONLY or not crosses:
            seen.append(ref)
    return [{"code": "element_not_representable_2d", "ref": ref} for ref in seen]
