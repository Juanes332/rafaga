"""comparability + comparability_key (job-contract.md 2.3, ADR-23)."""

import hashlib
import json
from typing import Any

from app.models.jobs.payload_schemas import HeavyPayload
from app.services.boundary.log_profile import friction_velocity, log_speed

NOMINAL_U10_MS = 10.0


def _round6(value: Any) -> Any:
    """Round every float in a nested structure to 6 decimals."""
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, dict):
        return {k: _round6(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_round6(v) for v in value]
    return value


def comparability(payload: HeavyPayload) -> dict[str, Any]:
    """Return the hashed fields; U_ref uses the nominal U10 = 10 m/s."""
    wind = payload.wind
    ustar = friction_velocity(NOMINAL_U10_MS, wind.z0_m, wind.kappa)
    uref = float(log_speed(wind.analysis_height_m, ustar, wind.z0_m, wind.kappa))
    output = payload.grid.output.model_dump(exclude_none=True)
    section = payload.section.model_dump() if payload.section else None
    return _round6({
        "kind": payload.job_kind, "direction_deg": float(wind.wind_from_deg),
        "z0_m": float(wind.z0_m), "uref_za_ms": uref, "dx_m": float(payload.grid.sim.dx_m),
        "output_grid": output, "analysis_height_m": float(wind.analysis_height_m),
        "section": section,
    })


def comparability_key(fields: dict[str, Any]) -> str:
    """Return sha256 hex of the canonical JSON (sorted keys)."""
    canonical = json.dumps(fields, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
