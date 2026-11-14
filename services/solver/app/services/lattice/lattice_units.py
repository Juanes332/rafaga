"""LBM unit conversion and stability parameters (ADR-14)."""

import math
from dataclasses import dataclass

NU_AIR_M2_S = 1.5e-5
RE_INDEPENDENCE = 2.0e4
RE_SHARP_EDGE = 1.1e4


@dataclass(frozen=True)
class LatticeUnits:
    """Lattice scales derived from the physical reference velocity."""

    u_lat: float
    dx_m: float
    dt_s: float
    nu_lat: float
    tau0: float


def lattice_units(u_lat: float, dx_m: float, u_phys_ms: float, nu_floor: float) -> LatticeUnits:
    """Return dt, the floored lattice viscosity and tau0 = 0.5 + 3 nu."""
    dt = u_lat * dx_m / u_phys_ms
    nu = max(NU_AIR_M2_S * dt / dx_m**2, nu_floor)
    return LatticeUnits(u_lat, dx_m, dt, nu, 0.5 + 3.0 * nu)


def tau_from_reynolds(u_lat: float, length_cells: float, reynolds: float) -> float:
    """Return tau for a prescribed Reynolds number (validation runs)."""
    return 0.5 + 3.0 * u_lat * length_cells / reynolds


def effective_reynolds(u_lat: float, height_cells: float, nu_lat: float) -> float:
    """Return the effective lattice building Reynolds number."""
    return u_lat * height_cells / nu_lat


def flow_through_steps(nx: int, u_lat: float) -> int:
    """Return the number of steps of one flow-through (ADR-11)."""
    return max(1, math.ceil(nx / u_lat))
