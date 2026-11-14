"""2D plan domain width: an equivalent of the 3D blockage rule (BR-16).

The contract grid gives the plan lattice 5H of lateral margin. In 2D
the buildings are infinitely tall, so the blockage is the cross-wind
width ratio W/Ly (about 20 % for a 50 m wide group), and free-slip
sides squeeze the flow around it: K > 1.2 bands reached the lateral
edges. The solver widens the lattice symmetrically until W/Ly <= 5 %;
the output grid, and hence comparability, is unchanged. Going from
5 % to 3.4 % changed the acceleration area by < 1 % in tests.
"""

import math

from app.models.jobs.payload_schemas import HeavyPayload
from app.services.voxelize.frame_transform import WindFrame

PLAN_BLOCKAGE_LIMIT = 0.05


def _frame(p: HeavyPayload) -> WindFrame:
    """Return the simulation frame of a payload."""
    sim = p.grid.sim
    return WindFrame.from_wind(sim.wind_from_deg if sim.wind_from_deg is not None
                               else p.wind.wind_from_deg)


def crosswind_width(p: HeavyPayload) -> float:
    """Return the cross-wind extent (m) of the base buildings' bounding box."""
    lo, hi = p.scene.bounds["base_min"], p.scene.bounds["base_max"]
    corners = [(x, y) for x in (lo[0], hi[0]) for y in (lo[1], hi[1])]
    frame = _frame(p)
    ys = [float(frame.to_sim(x, y)[1]) for x, y in corners]
    return max(ys) - min(ys)


def plan_blockage(p: HeavyPayload) -> float:
    """Return W / Ly of a plan payload."""
    sim = p.grid.sim
    return crosswind_width(p) / (int(sim.ny) * sim.dx_m)


def widened_payload(p: HeavyPayload) -> HeavyPayload:
    """Return the plan2d payload with a lattice wide enough, else p itself."""
    if p.job_kind != "plan2d" or plan_blockage(p) <= PLAN_BLOCKAGE_LIMIT:
        return p
    sim = p.grid.sim
    needed = crosswind_width(p) / PLAN_BLOCKAGE_LIMIT
    extra = math.ceil((needed - int(sim.ny) * sim.dx_m) / (2 * sim.dx_m))
    origin = list(sim.origin)
    origin[1] -= extra * sim.dx_m
    grid = p.grid.model_copy(update={"sim": sim.model_copy(
        update={"origin": origin, "ny": int(sim.ny) + 2 * extra})})
    return p.model_copy(update={"grid": grid})


# 3D domain top (deviation from contract 3.2's 6H only as a floor): the
# solver guarantees at least MIN_TOP_H building heights above ground so
# the free-slip top does not squeeze the flow over the roofs. Contract
# grids already give 6H (stretched for blockage); this only acts on
# older or hand-made payloads, raising the top as far as memory allows.
MIN_TOP_H = 5.0


def raised_top_payload(p: HeavyPayload, max_nodes: int | None) -> tuple[HeavyPayload, list[dict]]:
    """Return the volume3d payload with nz * dx >= MIN_TOP_H * H, and warnings."""
    sim = p.grid.sim
    if p.job_kind != "volume3d" or sim.nz is None:
        return p, []
    needed = math.ceil(round(MIN_TOP_H * p.scene.h_max_m / sim.dx_m, 6))
    if int(sim.nz) >= needed:
        return p, []
    layer = sim.nx * int(sim.ny)
    nz = needed if max_nodes is None else min(needed, max(int(sim.nz), max_nodes // layer))
    warnings = [] if nz == needed else [{"code": "domain_top_capped", "ref": p.scene.source_ref()}]
    grid = p.grid.model_copy(update={"sim": sim.model_copy(update={"nz": nz})})
    return p.model_copy(update={"grid": grid}), warnings
