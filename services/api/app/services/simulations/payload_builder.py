"""Heavy-job payloads exactly as job-contract.md section 3.3."""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.services.simulations import simulation_constants as c


@dataclass
class JobContext:
    """Everything one heavy job payload is made of."""

    kind: str
    project_id: UUID
    study_id: UUID
    job_id: UUID
    alternative_id: UUID
    scene: Mapping[str, Any]
    section: Mapping[str, Any] | None
    wind_from_deg: float
    u10_ms: float
    inputs: Mapping[str, Any]
    sim: Mapping[str, Any]
    output: Mapping[str, Any]
    device: str
    memory_bytes: int
    thresholds: Mapping[str, Any]


def wind_block(ctx: JobContext) -> dict[str, Any]:
    """Return the wind block with log-law derived speeds (ADR-20)."""
    z0, za = ctx.inputs["z0_m"], ctx.inputs["analysis_height_m"]
    ustar = c.KAPPA * ctx.u10_ms / math.log((10.0 + z0) / z0)
    uref = ustar / c.KAPPA * math.log((za + z0) / z0)
    return {
        "wind_from_deg": float(ctx.wind_from_deg), "u10_ms": float(ctx.u10_ms),
        "z0_m": z0, "analysis_height_m": za, "ustar_ms": round(ustar, 4),
        "uref_za_ms": round(uref, 4),
        "air_density_kg_m3": ctx.inputs["air_density_kg_m3"], "kappa": c.KAPPA,
    }


def build_heavy_payload(ctx: JobContext) -> dict[str, Any]:
    """Return the self-contained payload of one heavy job."""
    pid = str(ctx.project_id)
    return {
        "contract_version": 1, "job_kind": ctx.kind, "project_id": pid,
        "study_id": str(ctx.study_id), "alternative_id": str(ctx.alternative_id),
        "output_dir": f"results/{pid}/{ctx.study_id}/{ctx.job_id}",
        "scene": ctx.scene, "section": ctx.section, "wind": wind_block(ctx),
        "grid": {"sim": dict(ctx.sim), "output": dict(ctx.output)},
        "physics": c.physics(ctx.kind), "convergence": c.convergence(ctx.kind),
        "device": ctx.device,
        "memory": {"estimate_bytes": ctx.memory_bytes,
                   "bytes_per_node": c.BYTES_PER_NODE[ctx.kind],
                   "overhead_bytes": c.OVERHEAD_BYTES},
        "render": {"dpi": 150, "k_accel": ctx.thresholds["k_accel"],
                   "k_stagnation": ctx.thresholds["k_stagnation"]},
    }
