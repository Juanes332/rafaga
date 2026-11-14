"""Far-field profile nudging for the 3D LES (deviation, README "Turbulence").

The hybrid RANS/LES ground layer is not in exact equilibrium with the
log-law inflow: unforced, K at z_a drifted 10-15 % down along the fetch.
A PI controller compares the streamwise velocity averaged over the
lateral strips (the outer STRIP_FRACTION of each side, fluid cells
only, far from the buildings) with the target log profile for every
(z, x) and applies the correction as a body force on the whole (z, x)
line, like a large-scale pressure gradient. Wakes keep their own
dynamics: the force is uniform across y and changes over flow-through
times. Sponge columns and lines without strip fluid get no force.
"""

from dataclasses import dataclass

import numpy as np

from app.services.lattice.lattice_problem import POROUS, SOLID

STRIP_FRACTION = 0.1
UPDATE_EVERY = 20
P_FT, I_FT, EMA_FT = 0.5, 1.0, 0.1


@dataclass(frozen=True)
class NudgeSpec:
    """Host description of the controller; times in lattice steps."""

    target: np.ndarray  # (nz,) target streamwise velocity
    shape: tuple[int, int, int]  # (nz, ny, nx)
    strip_nodes: np.ndarray  # flat indices of strip fluid nodes
    strip_cell: np.ndarray  # (z * nx + x) of each strip node
    live: np.ndarray  # (nz * nx,) bool, lines that are controlled
    p_steps: float
    i_steps: float
    ema_steps: float
    every: int = UPDATE_EVERY


def nudge_spec(mask: np.ndarray, sponge: np.ndarray, target, ft_steps: int,
               fraction: float = STRIP_FRACTION) -> NudgeSpec:
    """Return the strips and gains for a (z, y, x) mask."""
    nz, ny, nx = mask.shape
    width = max(2, int(ny * fraction))
    strip = np.zeros(mask.shape, dtype=bool)
    strip[:, :width] = strip[:, ny - width:] = True
    strip &= (mask != SOLID) & (mask != POROUS)
    nodes = np.flatnonzero(strip.reshape(-1))
    z, x = nodes // (ny * nx), nodes % nx
    cell = (z * nx + x).astype(np.int64)
    has = np.bincount(cell, minlength=nz * nx) > 0
    live = has & np.tile(np.asarray(sponge) == 0, nz)
    # The force acts UPDATE_EVERY steps between updates: gains slower
    # than that by an order of magnitude keep the discrete loop stable.
    p_steps = max(P_FT * ft_steps, 10.0 * UPDATE_EVERY)
    i_steps = max(I_FT * ft_steps, 2.0 * p_steps)
    ema_steps = max(EMA_FT * ft_steps, float(UPDATE_EVERY))
    return NudgeSpec(np.asarray(target, dtype=np.float32), (nz, ny, nx), nodes.astype(np.int64),
                     cell, live, p_steps, i_steps, ema_steps)


class ProfileNudger:
    """Run the controller on host (NumPy) or device (CuPy) arrays."""

    def __init__(self, spec: NudgeSpec, xp, c_x: np.ndarray) -> None:
        """Upload the strips and start from zero error."""
        self.spec, self.xp = spec, xp
        nz, _, nx = spec.shape
        self.nodes = xp.asarray(spec.strip_nodes)
        self.cell = xp.asarray(spec.strip_cell)
        self.count = xp.maximum(xp.bincount(self.cell, minlength=nz * nx), 1).astype(xp.float32)
        self.live = xp.asarray(spec.live)
        self.target = xp.asarray(np.repeat(spec.target, nx).astype(np.float32))
        self.c_x = xp.asarray(np.asarray(c_x, dtype=np.float32))
        self.ema = self.target.copy()
        self.integral = xp.zeros_like(self.target)
        self.fxz = xp.zeros_like(self.target)

    def update(self, f) -> None:
        """Refresh fxz from the populations f (Q, N)."""
        xp, s = self.xp, self.spec
        g = f[:, self.nodes]
        ux = (self.c_x @ g) / g.sum(axis=0)
        mean = xp.bincount(self.cell, weights=ux, minlength=self.count.size) / self.count
        alpha = np.float32(min(1.0, s.every / s.ema_steps))
        self.ema += alpha * (mean.astype(xp.float32) - self.ema)
        error = xp.where(self.live, self.target - self.ema, 0).astype(xp.float32)
        self.integral += error * np.float32(s.every / s.i_steps)
        xp.clip(self.integral, -self.target, self.target, out=self.integral)
        self.fxz[:] = (error + self.integral) / np.float32(s.p_steps)
