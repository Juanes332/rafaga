"""Closed-form Lawson LDDC exceedance per cell (ADR-15)."""

import numpy as np


def transfer_factor(z_a: float, z0: float, z0_ref: float, h_b: float) -> float:
    """Return T taking ERA5 U10 (z0_ref) to U(z_a) over site roughness z0."""
    site = np.log((z_a + z0) / z0) / np.log(h_b / z0)
    era5 = np.log(h_b / z0_ref) / np.log((10.0 + z0_ref) / z0_ref)
    return float(site * era5)


def gust_factor(ti: np.ndarray) -> np.ndarray:
    """Return G = max(1, (1 + 3 I)/1.85) (GEM)."""
    return np.maximum(1.0, (1.0 + 3.0 * ti) / 1.85)


def sector_of(direction_deg: float, centers: list[float]) -> int:
    """Return the index of the sector [c - w/2, c + w/2) holding the direction."""
    width = 360.0 / len(centers)
    for i, c in enumerate(centers):
        if (direction_deg - c + width / 2) % 360.0 < width:
            return i
    return int(np.argmin([abs((direction_deg - c + 180) % 360 - 180) for c in centers]))


def exceedance(threshold_ms: float, sectors: list[dict], coverage: float) -> np.ndarray:
    """Return P(U_eff > U_t) per cell.

    Each sector dict carries frequency, weibull_k, weibull_c_ms, K
    (cell array), G (cell array) and T.
    """
    total = None
    for s in sectors:
        scale = s["G"] * s["K"] * s["T"] * s["weibull_c_ms"]
        with np.errstate(divide="ignore", invalid="ignore"):
            term = np.exp(-(threshold_ms / scale) ** s["weibull_k"])
        term = np.where(scale > 0, term, 0.0)
        total = s["frequency"] * term if total is None else total + s["frequency"] * term
    return total / max(coverage, 1e-12)


def comfort_class(probs: list[np.ndarray], limit: float) -> np.ndarray:
    """Return 0..3 for the first class with P <= limit, 4 (E) otherwise."""
    cls = np.full(probs[0].shape, len(probs), dtype=np.uint8)
    for i in reversed(range(len(probs))):
        cls = np.where(probs[i] <= limit, i, cls).astype(np.uint8)
    return cls
