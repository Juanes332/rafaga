"""Build the WindClimate response from a wind row."""

import math
from collections.abc import Mapping
from typing import Any

KAPPA = 0.41


def ustar_from(u10_ms: float | None, z0_m: float) -> float | None:
    """Return friction velocity for a U10, or None without one."""
    if u10_ms is None:
        return None
    return KAPPA * u10_ms / math.log((10.0 + z0_m) / z0_m)


def wind_response(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return the openapi WindClimate shape for a wind_climates row."""
    return {
        "source": row["source"],
        "rose": row["rose"],
        "period_years": row["period_years"],
        "manual_direction_deg": row["manual_direction_deg"],
        "manual_u10_ms": row["manual_u10_ms"],
        "terrain_category": row["terrain_category"],
        "z0_m": row["z0_m"],
        "ustar_ms": ustar_from(row["manual_u10_ms"], row["z0_m"]),
        "air_density_kg_m3": row["air_density_kg_m3"],
        "fetched_at": row["fetched_at"],
        "from_cache": False,
    }
