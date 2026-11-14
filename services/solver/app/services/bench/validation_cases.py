"""Versioned validation problems: square cylinder, porous channel, AIJ case A."""

import numpy as np

from app.services.boundary.log_profile import (
    lattice_inlet_profile, perturbation_bank, sponge_ramp, wall_drag_coefficient,
)
from app.services.lattice.lattice_problem import LatticeProblem
from app.services.lattice.lattice_units import tau_from_reynolds
from app.services.porous.porous_model import idelchik_zeta, screen_coefficient


def square_cylinder(d: int = 20, reynolds: float = 150.0, u: float = 0.1) -> tuple[LatticeProblem, dict]:
    """Return the 2D square cylinder at 5 % blockage (SOL-15) and its geometry."""
    ny, nx = 20 * d, 35 * d
    x0, y0 = 10 * d, ny // 2 - d // 2 + 1  # one-cell offset seeds the shedding
    mask = np.zeros((ny, nx), dtype=np.uint8)
    mask[y0 : y0 + d, x0 : x0 + d] = 1
    inlet = np.zeros((1, 2, ny), dtype=np.float32)
    inlet[0, 0] = u
    problem = LatticeProblem(
        shape=(ny, nx), mask=mask, pid=np.zeros((ny, nx), dtype=np.uint16),
        ptable=np.zeros((1, 5), dtype=np.float32), sponge=sponge_ramp(nx, 0.1), inlet=inlet,
        tau0=tau_from_reynolds(u, d, reynolds), smagorinsky_cs=0.0, sponge_tau=1.0,
    )
    return problem, {"x_rear": x0 + d, "y_mid": y0 + d // 2, "d": d, "u": u}


def porous_channel(beta: float, u: float = 0.02, nx: int = 240, ny: int = 8) -> tuple[LatticeProblem, dict]:
    """Return a free-slip channel crossed by one porous screen cell layer."""
    mask = np.zeros((ny, nx), dtype=np.uint8)
    pid = np.zeros((ny, nx), dtype=np.uint16)
    xs = nx // 2
    mask[:, xs], pid[:, xs] = 2, 1
    zeta = float(idelchik_zeta(beta))
    ptable = np.zeros((2, 5), dtype=np.float32)
    ptable[1] = [screen_coefficient(zeta, 1.0), 1.0, 0.0, 0.0, 0.0]
    inlet = np.zeros((1, 2, ny), dtype=np.float32)
    inlet[0, 0] = u
    problem = LatticeProblem(
        shape=(ny, nx), mask=mask, pid=pid, ptable=ptable, sponge=np.zeros(nx, dtype=np.float32),
        inlet=inlet, tau0=0.56, smagorinsky_cs=0.0,
    )
    return problem, {"x_screen": xs, "zeta": zeta, "u": u}


def aij_case_a(b: int = 10, z0_cells: float = 0.01, seed: int = 7) -> tuple[LatticeProblem, dict]:
    """Return the 1:1:2 building (b x b x 2b) in a log-law ABL (SOL-16)."""
    h = 2 * b
    nz, ny, nx = 4 * h, 6 * h + b, 3 * h + b + 8 * h
    x0, y0 = 3 * h, (ny - b) // 2
    mask = np.zeros((nz, ny, nx), dtype=np.uint8)
    mask[:h, y0 : y0 + b, x0 : x0 + b] = 1
    profile = lattice_inlet_profile(nz, 1.0, z0_cells, 0.05)
    base = np.zeros((3, nz * ny), dtype=np.float32)
    base[0] = np.repeat(profile, ny)
    inlet = perturbation_bank(base, 0.02, seed)
    problem = LatticeProblem(
        shape=(nz, ny, nx), mask=mask, pid=np.zeros(mask.shape, dtype=np.uint16),
        ptable=np.zeros((1, 5), dtype=np.float32), sponge=sponge_ramp(nx, 0.1), inlet=inlet,
        tau0=0.50015, smagorinsky_cs=0.17, bottom_wall=True,
        a_wall=wall_drag_coefficient(1.0, z0_cells), initial_u=base,
    )
    return problem, {"x0": x0, "y_mid": y0 + b // 2, "b": b, "h": h}
