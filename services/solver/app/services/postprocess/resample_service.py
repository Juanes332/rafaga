"""Sample averaged sim fields onto the output grid (job-contract 3.2 rule 5)."""

import numpy as np

from app.services.voxelize.coverage_service import AxisGrid
from app.services.voxelize.frame_transform import WindFrame


def blend_layers(fields: dict[str, np.ndarray], fluid: np.ndarray, z: float, dx: float,
                 z0: float | None = None, quadratic: tuple[str, ...] = ("u2",)):
    """Return 2D fields interpolated at height z from 3D ones.

    With z0 the interpolation is linear in eta = ln((z + z0)/z0), exact
    for the log law of the wall function; under the first cell centre it
    extrapolates U(z) = U_1 eta(z)/eta(z_1) (fields in `quadratic`, the
    mean square, scale with the square). Without z0 it is linear in z.
    Solid layers get zero weight; a point with no fluid support is
    reported as non-fluid.
    """
    nz = fluid.shape[0]
    zc = (np.arange(nz) + 0.5) * dx
    if z0 is not None and z < zc[0]:
        r = float(np.log((z + z0) / z0) / np.log((zc[0] + z0) / z0))
        out = {name: f[0] * (r * r if name in quadratic else r) for name, f in fields.items()}
        return out, fluid[0] > 0
    fz = min(max(z / dx - 0.5, 0.0), nz - 1.0)
    k0 = int(np.floor(fz))
    k1 = min(k0 + 1, nz - 1)
    w1 = fz - k0
    if z0 is not None and k1 > k0:
        eta = np.log((np.array([zc[k0], z, zc[k1]]) + z0) / z0)
        w1 = float((eta[1] - eta[0]) / (eta[2] - eta[0]))
    a = (1 - w1) * fluid[k0]
    b = w1 * fluid[k1]
    total = a + b
    safe = np.where(total > 0, total, 1.0)
    out = {name: (a * f[k0] + b * f[k1]) / safe for name, f in fields.items()}
    return out, total > 0


def bilinear(fields: dict[str, np.ndarray], fluid: np.ndarray, sim: AxisGrid,
             frame: WindFrame, east: np.ndarray, north: np.ndarray) -> dict[str, np.ndarray]:
    """Return fields sampled at ENU points; NaN where no fluid support."""
    xs, ys = frame.to_sim(east, north)
    fx = (xs - sim.x0) / sim.dx - 0.5
    fy = (ys - sim.y0) / sim.dx - 0.5
    i0, j0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
    wx, wy = fx - i0, fy - j0
    inside = (fx >= -0.5) & (fx <= sim.nx - 0.5) & (fy >= -0.5) & (fy <= sim.ny - 0.5)
    acc = {name: np.zeros(east.shape) for name in fields}
    weight = np.zeros(east.shape)
    for di, dj, w in ((0, 0, (1 - wx) * (1 - wy)), (1, 0, wx * (1 - wy)),
                      (0, 1, (1 - wx) * wy), (1, 1, wx * wy)):
        ii = np.clip(i0 + di, 0, sim.nx - 1)
        jj = np.clip(j0 + dj, 0, sim.ny - 1)
        ww = w * fluid[jj, ii]
        weight += ww
        for name, f in fields.items():
            acc[name] += ww * f[jj, ii]
    ok = inside & (weight > 1e-9)
    return {name: np.where(ok, v / np.where(ok, weight, 1.0), np.nan) for name, v in acc.items()}


def plan_points(origin_x: float, origin_y: float, dx: float, nx: int, ny: int):
    """Return ENU cell-centre coordinates (ny, nx) of a north-up grid."""
    xs = origin_x + (np.arange(nx) + 0.5) * dx
    ys = origin_y + (np.arange(ny) + 0.5) * dx
    return np.meshgrid(xs, ys)
