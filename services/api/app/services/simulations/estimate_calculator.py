"""Memory estimate and automatic coarsening (ADR-10)."""

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from shapely.geometry import Polygon

from app.services.simulations import simulation_constants as c
from app.services.simulations.grid_service import node_count

# A grid builder maps dx to the (sim, output) grids of every job.
GridBuilder = Callable[[float], list[tuple[dict[str, Any], dict[str, Any]]]]


@dataclass
class Estimate:
    """Result of the estimate; dx_used is what the study will run at."""

    device: str
    nodes: int
    memory_bytes: int
    budget_bytes: int
    fits: bool
    proposed_dx_m: float | None
    rejected_reason: str | None
    eta_seconds: int
    grid: dict[str, Any]
    dx_used: float


def smallest_building_width(scene: Mapping[str, Any]) -> float | None:
    """Return the narrowest side of any building prism in metres."""
    widths = []
    for solid in scene["solids"]:
        if solid["origin"]["kind"] not in ("building", "building_tier"):
            continue
        rect = Polygon(solid["footprint"]).minimum_rotated_rectangle
        pts = list(rect.exterior.coords)
        widths.append(min(math.dist(pts[0], pts[1]), math.dist(pts[1], pts[2])))
    return min(widths) if widths else None


def pick_device(requested: str, node: Mapping[str, Any]) -> tuple[str, str | None]:
    """Return the device to use and a reason when it is unusable."""
    device = node["device"] if requested == "auto" else requested
    if device == "gpu" and (node["device"] != "gpu" or not node["vram_total_bytes"]):
        return "gpu", "device_unavailable"
    return device, None


def budget_for(device: str, kind: str, node: Mapping[str, Any], cpu_cap: int) -> int:
    """Return the memory budget in bytes for the chosen device."""
    if device == "gpu":
        return max(0, int(c.GPU_VRAM_FRACTION * node["vram_total_bytes"] - c.OVERHEAD_BYTES))
    budget = int(node["ram_budget_bytes"])
    if kind == "volume3d":
        budget = min(budget, cpu_cap * c.BYTES_PER_NODE[kind] + c.OVERHEAD_BYTES)
    return budget


def _memory(kind: str, grids: Sequence[tuple[dict, dict]]) -> tuple[int, int]:
    """Return (largest node count, memory bytes for it)."""
    nodes = max(node_count(sim) for sim, _ in grids)
    return nodes, nodes * c.BYTES_PER_NODE[kind] + c.OVERHEAD_BYTES


def model_seconds(kind: str, sims: Sequence[dict[str, Any]], node: Mapping[str, Any]) -> float:
    """Return the modelled wall time of all jobs; see the time model in simulation_constants."""
    mlups = node["mlups_3d"] if kind == "volume3d" else node["mlups_2d"]
    if not mlups:
        mlups = c.CPU_FALLBACK_MLUPS[kind]
    conv = c.convergence(kind)
    steps_per_nx = (conv["spinup_ft"] + conv["min_avg_ft"]) / c.U_LATTICE_REF * c.STEP_SCALE[kind]
    total = 0.0
    for sim in sims:
        n = node_count(sim)
        eff = c.PEAK_FRACTION[kind] * mlups * n / (n + c.N_HALF_NODES[kind])
        total += c.FIXED_OVERHEAD_S[kind] + steps_per_nx * sim["nx"] * n / (eff * 1e6)
    return total


def _eta(kind: str, grids: Sequence[tuple[dict, dict]], node: Mapping[str, Any]) -> int:
    """Return the study ETA in whole seconds."""
    return math.ceil(model_seconds(kind, [sim for sim, _ in grids], node))


def _coarsen(kind: str, dx: float, budget: int, build: GridBuilder, mem: int) -> float | None:
    """Return the smallest 0.25 m multiple of dx that fits, or None."""
    if budget <= c.OVERHEAD_BYTES:
        return None
    exp = 1 / (3 if kind == "volume3d" else 2)
    proposed = math.ceil(dx * (mem / budget) ** exp / c.DX_STEP) * c.DX_STEP
    for _ in range(400):
        if _memory(kind, build(proposed))[1] <= budget:
            return proposed
        proposed += c.DX_STEP
    return None


def _finest_legal(width: float, budget: int, kind: str, build: GridBuilder) -> float | None:
    """Return the coarsest dx keeping the minimum cells per building that also fits memory."""
    cap = math.floor(round(width / c.MIN_BUILDING_CELLS / c.DX_STEP, 6)) * c.DX_STEP
    if cap < c.DX_STEP or _memory(kind, build(cap))[1] > budget:
        return None
    return cap


def _grid_view(grids: Sequence[tuple[dict, dict]]) -> dict[str, Any]:
    """Return the grid summary of the first job."""
    return {"sim": grids[0][0], "output": grids[0][1]}


def _empty(kind: str, device: str, reason: str, grids: Sequence, dx: float) -> Estimate:
    """Return a not-fitting estimate with no budget."""
    nodes, mem = _memory(kind, grids)
    return Estimate(device, nodes, mem, 0, False, None, reason, 0, _grid_view(grids), dx)


def compute_estimate(
    kind: str, scene: Mapping[str, Any], dx: float, requested: str,
    node: Mapping[str, Any] | None, cpu_cap: int, build: GridBuilder,
) -> Estimate:
    """Estimate memory, ETA and coarsening for a study request."""
    grids = build(dx)
    if node is None or not node["online"]:
        return _empty(kind, "gpu" if requested == "gpu" else "cpu", "solver_offline", grids, dx)
    device, unusable = pick_device(requested, node)
    if unusable:
        return _empty(kind, device, unusable, grids, dx)
    budget = budget_for(device, kind, node, cpu_cap)
    nodes, mem = _memory(kind, grids)
    proposed = None if mem <= budget else _coarsen(kind, dx, budget, build, mem)
    used = dx if mem <= budget else proposed
    reason = None if used else "mesh_too_large"
    width = smallest_building_width(scene)
    if used and width is not None and width / used < c.MIN_BUILDING_CELLS:
        reason = "buildings_too_small"
        proposed = _finest_legal(width, budget, kind, build)
    fits = mem <= budget and reason is None
    final = build(used or dx)
    return Estimate(device, nodes, mem, budget, fits, proposed, reason,
                    _eta(kind, final, node), _grid_view(grids), used or dx)
