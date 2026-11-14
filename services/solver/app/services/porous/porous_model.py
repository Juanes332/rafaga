"""Porous resistance coefficients in lattice units (ADR-13)."""

import numpy as np


def idelchik_zeta(beta) -> np.ndarray:
    """Return zeta(beta) for a thin sharp-edged perforated plate."""
    beta = np.asarray(beta, dtype=np.float64)
    return ((0.707 * np.sqrt(1.0 - beta) + 1.0 - beta) / beta) ** 2


def screen_coefficient(zeta: float, thickness_cells: float, coverage: float = 1.0) -> float:
    """Return a in F_n = -rho a |u_n| u_n spread over the layer thickness."""
    return float(zeta * coverage / (2.0 * max(thickness_cells, 1.0)))


def vegetation_coefficient(drag_coefficient: float, lad_m2_m3: float, dx_m: float,
                           coverage: float = 1.0) -> float:
    """Return a in F = -rho a |u| u with LAD converted to lattice units."""
    return float(drag_coefficient * lad_m2_m3 * dx_m * coverage)
