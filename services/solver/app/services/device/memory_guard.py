"""Pre-run memory check against the live device budget (ADR-10, SOL-19)."""

import math

from app.core.errors.solver_errors import MeshTooLargeError

BYTES_PER_NODE = {2: 104, 3: 224}
OVERHEAD_BYTES = 512 * 1024 * 1024
LOW_RAM_BYTES = 16 * 1024**3


def gpu_budget(total: int, free: int, fraction: float) -> int:
    """Return min(fraction x VRAM - 512 MiB, free now) in bytes."""
    return max(0, min(int(fraction * total) - OVERHEAD_BYTES, free))


def cpu_node_cap(dim: int, cap_3d: int, ram_total: int) -> int | None:
    """Return the CPU 3D node cap (1.5e6 below 16 GB of RAM), None in 2D."""
    if dim != 3:
        return None
    return min(cap_3d, 1_500_000) if ram_total < LOW_RAM_BYTES else cap_3d


def proposed_dx(dx: float, ratio: float, dim: int) -> float:
    """Return dx * ratio^(1/d) rounded up to 0.25 m."""
    return math.ceil(dx * ratio ** (1.0 / dim) / 0.25 - 1e-9) * 0.25


def check_memory(nodes: int, dim: int, dx: float, budget: int, node_cap: int | None = None,
                 bytes_per_node: int | None = None) -> int:
    """Return the needed bytes or raise mesh_too_large with a proposed dx."""
    per_node = bytes_per_node or BYTES_PER_NODE[dim]
    need = nodes * per_node + OVERHEAD_BYTES
    ratio = need / max(budget, 1)
    if node_cap is not None and nodes > node_cap:
        ratio = max(ratio, nodes / node_cap)
    if ratio <= 1.0:
        return need
    dx_new = proposed_dx(dx, ratio, dim)
    raise MeshTooLargeError(
        f"mesh needs {need} bytes but the device budget is {budget}; try dx_m={dx_new}",
        {"needed_bytes": need, "budget_bytes": budget, "proposed_dx_m": dx_new},
    )
