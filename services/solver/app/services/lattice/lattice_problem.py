"""Device-neutral description of one lattice run (host NumPy arrays)."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

from app.services.lattice.lattice_constants import Lattice, lattice_for_dim

if TYPE_CHECKING:
    from app.services.boundary.profile_nudging import NudgeSpec

SOLID = 1
POROUS = 2
# Columns of the porous table: a_screen, n_x, n_y, n_z, a_vegetation.
PTABLE_COLUMNS = 5


@dataclass
class LatticeProblem:
    """Everything a stepper needs; arrays are row-major (z, y, x)."""

    shape: tuple[int, ...]
    mask: np.ndarray  # uint8, 0 fluid, 1 solid, 2 porous
    pid: np.ndarray  # uint16 porous table row, 0 = none
    ptable: np.ndarray  # float32 (n, 5); row 0 all zeros
    sponge: np.ndarray  # float32 (nx,) ramp weight 0..1
    inlet: np.ndarray  # float32 (K, dim, rows) inlet velocity bank
    tau0: float
    smagorinsky_cs: float
    tau_min: float = 0.5005
    tau_max: float = 2.0
    sponge_tau: float = 1.0
    bottom_wall: bool = False
    a_wall: float = 0.0
    inlet_period: int = 20
    initial_u: np.ndarray | None = field(default=None)  # (dim, rows)
    # Equilibrium ABL closure (boundary/abl_closure.py): per-node mixing
    # length (lattice units, None = uniform C_s), specular ground under the
    # wall-function drag, and a streamwise shear force on the top layer.
    mixing_length: np.ndarray | None = field(default=None)
    ground_slip: bool = False
    top_force: float = 0.0
    # 3D LES only: far-field profile controller (boundary/profile_nudging.py).
    nudge: "NudgeSpec | None" = field(default=None)

    @property
    def dim(self) -> int:
        """Return the spatial dimension."""
        return len(self.shape)

    @property
    def lattice(self) -> Lattice:
        """Return the velocity set for this dimension."""
        return lattice_for_dim(self.dim)

    @property
    def nodes(self) -> int:
        """Return the total node count."""
        return int(np.prod(self.shape))

    @property
    def nx(self) -> int:
        """Return the streamwise node count."""
        return int(self.shape[-1])

    @property
    def ground_bounce(self) -> bool:
        """Return True when the ground bounces back (no wall-function slip)."""
        return self.bottom_wall and not self.ground_slip

    def length_scale_sq(self) -> np.ndarray:
        """Return the flat float32 (C_s dx)^2 or max(l, C_s)^2 per node."""
        cs = np.float32(self.smagorinsky_cs)
        if self.mixing_length is None:
            return np.full(self.nodes, cs * cs, dtype=np.float32)
        lm = np.maximum(self.mixing_length.reshape(-1).astype(np.float32), cs)
        return lm * lm

    @property
    def rows(self) -> int:
        """Return the number of streamwise rows (y, or z*y)."""
        return self.nodes // self.nx


def equilibrium(lat: Lattice, rho: np.ndarray, u: np.ndarray) -> np.ndarray:
    """Return f_eq (Q, N) in float32 for density (N,) and velocity (dim, N)."""
    c = lat.c.astype(np.float32)
    w = lat.w.astype(np.float32)[:, None]
    cu = c @ u
    usq = (u * u).sum(axis=0)
    return w * rho * (1 + 3 * cu + 4.5 * cu * cu - 1.5 * usq)


def initial_populations(problem: LatticeProblem) -> np.ndarray:
    """Return f (Q, N) at rest density with the inlet velocity copied downstream."""
    lat = problem.lattice
    n = problem.nodes
    u = np.zeros((problem.dim, n), dtype=np.float32)
    start = problem.inlet[0] if problem.initial_u is None else problem.initial_u
    u[:] = np.repeat(start, problem.nx, axis=1)
    u[:, problem.mask.reshape(-1) == SOLID] = 0
    return equilibrium(lat, np.ones(n, dtype=np.float32), u).astype(np.float32)
