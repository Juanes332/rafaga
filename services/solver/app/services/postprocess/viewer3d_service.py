"""Vertical slices and mean-flow streamlines for the 3D viewer (SOL-09)."""

from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates

from app.services.lattice.lattice_problem import SOLID
from app.services.postprocess.output_fields import uref_za_ms
from app.services.simulation.simulation_case import SimulationCase

MAX_LINES, MAX_POINTS = 400, 500


def centre_index(case: SimulationCase) -> tuple[int, int]:
    """Return sim (ix, iy) closest to the centre of the base buildings."""
    b = case.payload.scene.bounds
    cx = 0.5 * (b["base_min"][0] + b["base_max"][0])
    cy = 0.5 * (b["base_min"][1] + b["base_max"][1])
    xs, ys = case.frame.to_sim(cx, cy)
    sim = case.payload.grid.sim
    ix = int(np.clip((xs - sim.origin[0]) / sim.dx_m, 0, sim.nx - 1))
    iy = int(np.clip((ys - sim.origin[1]) / sim.dx_m, 0, sim.ny - 1))
    return ix, iy


def _to_enu(case: SimulationCase, ix, iy) -> tuple[np.ndarray, np.ndarray]:
    """Return ENU coordinates of fractional sim cell-centre indices."""
    sim = case.payload.grid.sim
    xs = sim.origin[0] + (np.asarray(ix) + 0.5) * sim.dx_m
    ys = sim.origin[1] + (np.asarray(iy) + 0.5) * sim.dx_m
    return case.frame.to_enu_vector(xs, ys)


def _streamlines(case: SimulationCase, u: np.ndarray, solid: np.ndarray) -> list:
    """Integrate RK2 streamlines through the mean field from upstream seeds."""
    nz, ny, nx = solid.shape
    h = case.payload.scene.h_max_m / case.payload.grid.sim.dx_m
    ix, iy = centre_index(case)
    ys = np.linspace(max(iy - 2 * h, 1), min(iy + 2 * h, ny - 2), 20)
    zs = np.linspace(0.5, min(1.5 * h, nz - 2), 10)
    gy, gz = np.meshgrid(ys, zs)
    pts = np.stack([gz.ravel(), gy.ravel(), np.full(gy.size, max(ix - 3 * h, 1.0))])
    lines = [[p.copy()] for p in pts.T][:MAX_LINES]
    alive = np.ones(pts.shape[1], dtype=bool)
    for _ in range(MAX_POINTS - 1):
        vel = np.stack([map_coordinates(c, pts, order=1, mode="nearest") for c in u])
        mid = pts + 0.5 * _unit(vel)
        vel = np.stack([map_coordinates(c, mid, order=1, mode="nearest") for c in u])
        pts = pts + _unit(vel)
        inside = (pts[0] >= 0) & (pts[0] < nz) & (pts[1] >= 0) & (pts[1] < ny) & (pts[2] >= 0) & (pts[2] < nx - 1)
        hit = map_coordinates(solid.astype(float), np.clip(pts, 0, None), order=0, mode="nearest") > 0.5
        alive &= inside & ~hit
        for k in np.flatnonzero(alive):
            lines[k].append(pts[:, k].copy())
    return [_line_enu(case, np.array(line)) for line in lines if len(line) > 2]


def _unit(vel: np.ndarray) -> np.ndarray:
    """Return a half-cell step along the velocity (z, y, x order)."""
    zyx = np.stack([vel[2], vel[1], vel[0]])
    norm = np.linalg.norm(zyx, axis=0)
    return 0.5 * zyx / np.where(norm > 1e-12, norm, 1.0)


def _line_enu(case: SimulationCase, line: np.ndarray) -> list[list[float]]:
    """Return a streamline as [[E, N, z], ...] rounded to centimetres."""
    east, north = _to_enu(case, line[:, 2], line[:, 1])
    z = (line[:, 0] + 0.5) * case.payload.grid.sim.dx_m
    return np.round(np.stack([east, north, z], axis=1), 2).tolist()


def write_viewer(case: SimulationCase, avg_u: np.ndarray, out_dir: Path) -> dict:
    """Write volume/slice_*.f32 and return the viewer3d.json document."""
    sim = case.payload.grid.sim
    solid = case.problem.mask == SOLID
    speed = np.sqrt((avg_u**2).sum(axis=0)) / case.u_ref_lat * uref_za_ms(case)
    speed = np.where(solid, np.nan, speed).astype(np.float32)
    ix, iy = centre_index(case)
    vol = out_dir / "volume"
    vol.mkdir(parents=True, exist_ok=True)
    speed[:, iy, :].astype("<f4").tofile(vol / "slice_xz.f32")
    speed[:, :, ix].astype("<f4").tofile(vol / "slice_yz.f32")
    nz, ny, nx = solid.shape
    top = nz * sim.dx_m
    e0, n0 = _to_enu(case, -0.5, iy)
    e1, n1 = _to_enu(case, nx - 0.5, iy)
    f0, m0 = _to_enu(case, ix, -0.5)
    f1, m1 = _to_enu(case, ix, ny - 0.5)
    slices = [
        {"name": "xz", "plane": {"axis": "y", "value_m": round(float(sim.origin[1] + (iy + 0.5) * sim.dx_m), 3)},
         "extents": [float(e0), float(n0), float(e1), float(n1), 0.0, top], "field": "slice_xz", "shape": [nz, nx]},
        {"name": "yz", "plane": {"axis": "x", "value_m": round(float(sim.origin[0] + (ix + 0.5) * sim.dx_m), 3)},
         "extents": [float(f0), float(m0), float(f1), float(m1), 0.0, top], "field": "slice_yz", "shape": [nz, ny]},
    ]
    return {"slices": slices, "streamlines": _streamlines(case, avg_u, solid), "frame": "local_enu"}
