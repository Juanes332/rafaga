"""Zone areas over a K field with numpy (BR-02..BR-04)."""

import numpy as np


def _zone(name: str, mask: np.ndarray, cell: float, fluid: float) -> dict[str, float | str]:
    """Build one zone entry from a boolean mask."""
    area = float(mask.sum()) * cell
    return {"zone": name, "area_m2": area, "percent": 100.0 * area / fluid if fluid else 0.0}


def fluid_area(k: np.ndarray, dx: float) -> float:
    """Return the area of finite (non-solid) cells."""
    return float(np.isfinite(k).sum()) * dx * dx


def compute_zones(k: np.ndarray, dx: float, k_accel: float, k_stagnation: float) -> list[dict]:
    """Return acceleration and stagnation zones; NaN cells never count."""
    cell, fluid = dx * dx, fluid_area(k, dx)
    with np.errstate(invalid="ignore"):
        return [_zone("acceleration", k >= k_accel, cell, fluid),
                _zone("stagnation", k <= k_stagnation, cell, fluid)]


def reduction_zone(ka: np.ndarray, kb: np.ndarray, dx: float, dk: float) -> dict:
    """Return the area where K_b - K_a falls below dk (dk is negative)."""
    with np.errstate(invalid="ignore"):
        mask = (kb - ka) < dk
    return _zone("reduction", mask, dx * dx, fluid_area(ka, dx))
