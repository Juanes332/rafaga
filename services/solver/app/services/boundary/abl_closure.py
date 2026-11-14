"""Equilibrium ABL closure: wall-distance mixing length and top shear.

A coarse LES (H/dx ~ 10) cannot carry the surface-layer stress u*^2 with
the Smagorinsky length C_s dx, so the log-law inflow decays along the
fetch. Prandtl's mixing length l = kappa (d + z0) gives nu_t = kappa u* (z + z0)
for the log profile, i.e. constant stress u*^2; with the matched wall
drag at the ground and the same stress applied at the top, the empty
domain keeps the inlet profile (Richards & Hoxey 1993).
"""

import numpy as np
from scipy.ndimage import distance_transform_edt

from app.services.lattice.lattice_problem import SOLID

KAPPA = 0.41


def mixing_length_field(mask: np.ndarray, dx: float, z0: float, floor: float,
                        ground: bool = True, cap_m: float | None = None,
                        kappa: float = KAPPA) -> np.ndarray:
    """Return l (lattice units) = kappa * min(z + z0, d_wall), at least `floor`.

    `mask` is (z, y, x), (z, s) or (y, x) with axis 0 vertical when
    `ground` is True. d_wall is the distance from a cell centre to the
    nearest solid face; porous cells are not walls.
    """
    solid = mask == SOLID
    dist = np.full(mask.shape, np.inf)
    if solid.any():
        dist = (distance_transform_edt(~solid) - 0.5) * dx
    if ground:
        z = (np.arange(mask.shape[0]) + 0.5) * dx + z0
        dist = np.minimum(dist, z.reshape((-1,) + (1,) * (mask.ndim - 1)))
    if cap_m is not None:
        dist = np.minimum(dist, cap_m)
    length = kappa * np.where(np.isfinite(dist), dist, 0.0) / dx
    return np.maximum(length, floor).astype(np.float32)


def top_shear_stress(rows: int, dx: float, z0: float, u_lat: float, kappa: float = KAPPA) -> float:
    """Return u*^2 (lattice) of the inlet log profile scaled to u_lat at the top."""
    ustar = kappa * u_lat / np.log((rows * dx + z0) / z0)
    return float(ustar * ustar)


# Hybrid RANS/LES (3D): the first RANS_LAYERS cells keep a damped
# mixing length because a coarse LES cannot resolve the eddies that
# carry the wall stress there; above, plain Smagorinsky (C_s dx) lets
# the resolved inflow turbulence survive. The resolved stress adds to
# the modelled one in the RANS layer, hence RANS_FACTOR < 1 (calibrated
# on the empty domain, README "Turbulence").
RANS_LAYERS = 6
RANS_FACTOR = 0.8


def hybrid_length_field(mask: np.ndarray, dx: float, z0: float, cs: float,
                        rans_layers: int = RANS_LAYERS,
                        factor: float = RANS_FACTOR) -> np.ndarray:
    """Return l (lattice units): factor * mixing length near ground, C_s above."""
    rans = factor * mixing_length_field(mask, dx, z0, cs)
    layer = np.arange(mask.shape[0]).reshape((-1,) + (1,) * (mask.ndim - 1))
    return np.where(layer < rans_layers, np.maximum(rans, cs), cs).astype(np.float32)
