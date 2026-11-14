"""Rasterize canonical scenes onto plan, section and volume grids (SOL-06)."""

from dataclasses import dataclass

import numpy as np
from shapely import affinity

from app.models.scene.scene_schemas import Porous, Scene, Solid
from app.services.porous.porous_model import screen_coefficient, vegetation_coefficient
from app.services.voxelize.coverage_service import (
    AxisGrid,
    interval_coverage,
    line_intervals,
    polygon_coverage,
)
from app.services.voxelize.frame_transform import WindFrame
from app.services.voxelize.primitive_geometry import (
    footprint,
    is_vertically_thin,
    thickened_screen,
    thin_normal,
    thin_width,
)
from app.services.voxelize.voxel_accumulator import VoxelAccumulator

_PLATE_FULL = 0.9  # cells within 10 % of the plate's best coverage count as fully crossed


@dataclass(frozen=True)
class Voxels:
    """Rasterized scene: mask, porous ids and the porous table."""

    mask: np.ndarray
    pid: np.ndarray
    ptable: np.ndarray


@dataclass(frozen=True)
class PlanSpec:
    """A plan grid in some frame, optionally with vertical layers."""

    grid: AxisGrid
    frame: WindFrame
    samples: int = 4
    z_levels: int | None = None  # None: single plan slice at z_a


def _sim_normal(frame: WindFrame, normal_enu) -> tuple[float, float, float]:
    """Rotate a horizontal ENU normal into the grid frame."""
    vx, vy = frame.to_sim(normal_enu[0], normal_enu[1])
    return float(vx), float(vy), 0.0


def _plan_window(spec: PlanSpec, poly) -> tuple[tuple[slice, slice], np.ndarray]:
    """Return the coverage window of an ENU polygon in the grid frame."""
    moved = affinity.affine_transform(poly, spec.frame.affine())
    return polygon_coverage(moved, spec.grid, spec.samples)


def _z_window(prism, spec: PlanSpec, z_a: float) -> tuple[slice, np.ndarray] | None:
    """Return the vertical layers covered by a prism (None if none)."""
    if spec.z_levels is None:
        inside = prism.z_min <= z_a <= prism.z_max
        return (slice(None), np.ones(1, dtype=np.float32)) if inside else None
    zc = interval_coverage(prism.z_min, prism.z_max, 0.0, spec.grid.dx, spec.z_levels, spec.samples)
    nz = np.flatnonzero(zc)
    if nz.size == 0:
        return None
    return slice(nz[0], nz[-1] + 1), zc[nz[0] : nz[-1] + 1]


def _expand(window2d, cov2d, zwin, spec: PlanSpec):
    """Combine plan and vertical coverage into an accumulator window."""
    if spec.z_levels is None:
        return window2d, cov2d
    zslice, zc = zwin
    return (zslice,) + window2d, zc[:, None, None] * cov2d[None]


def _add_solid(acc, spec, solid: Solid, z_a: float, threshold: float) -> None:
    """Rasterize one impermeable prism; sub-cell plates go through add_plate."""
    zwin = _z_window(solid, spec, z_a)
    if zwin is None:
        return
    poly = footprint(solid)
    window, cov = _plan_window(spec, poly)
    if cov.size == 0:
        return
    dx = spec.grid.dx
    if spec.z_levels is not None and is_vertically_thin(solid, dx, poly):
        normal, thickness = (0.0, 0.0, 1.0), solid.z_max - solid.z_min
    else:
        normal, thickness = _sim_normal(spec.frame, thin_normal(poly)), thin_width(poly)
    win, c = _expand(window, cov, zwin, spec)
    if 0 < thickness < threshold * dx:
        # Supersampling quantizes a 0.15 m plate's volume share, so the
        # in-plane fraction is taken relative to the best-covered cell.
        acc.add_plate(win, np.minimum(c / (_PLATE_FULL * c.max()), 1.0).astype(np.float32), normal)
        return
    acc.add_solid(win, c, normal)


def _add_porous(acc, spec, item: Porous, z_a: float) -> None:
    """Rasterize one screen or vegetation volume."""
    zwin = _z_window(item, spec, z_a)
    if zwin is None:
        return
    dx = spec.grid.dx
    if item.model == "vegetation":
        window, cov = _plan_window(spec, footprint(item))
        if cov.size:
            win, c = _expand(window, cov, zwin, spec)
            a = vegetation_coefficient(item.drag_coefficient or 0.2, item.lad_m2_m3 or 0.0, dx)
            acc.add_vegetation(win, (a * c).astype(np.float32))
        return
    win, c, width = _screen_band(acc, spec, item, zwin)
    if c.size:
        a = screen_coefficient(item.loss_coefficient or 0.0, width / dx, 1.0)
        normal = _sim_normal(spec.frame, item.normal or thin_normal(footprint(item)))
        acc.add_screen(win, (a * c).astype(np.float32), normal)


def _screen_band(acc, spec: PlanSpec, item: Porous, zwin):
    """Return the screen band (window, coverage, width) losing least to walls.

    The band is one cell wide; a celosia 0.5 m off a facade centred in it
    reached into the wall, and the wall cells dropped up to half of its
    drag. Of the centred and the two one-sided bands, the one whose
    coverage falls least on cells already solid is kept (centred on ties).
    """
    best = None
    for side in (0, 1, -1):
        poly, width = thickened_screen(item, spec.grid.dx, side)
        window, cov = _plan_window(spec, poly)
        if cov.size == 0:
            continue
        win, c = _expand(window, cov, zwin, spec)
        lost = float((c * (acc.solid[win] >= acc.threshold)).sum())
        if best is None or lost < best[0] - 1e-6:
            best = (lost, win, c, width)
    if best is None:
        return None, np.zeros(0, dtype=np.float32), spec.grid.dx
    return best[1], best[2], best[3]


def voxelize_plan(scene: Scene, spec: PlanSpec, threshold: float = 0.5) -> Voxels:
    """Rasterize a plan slice at z_a (z_levels None) or a 3D volume."""
    shape = (spec.grid.ny, spec.grid.nx)
    if spec.z_levels is not None:
        shape = (spec.z_levels,) + shape
    acc = VoxelAccumulator(shape, threshold)
    z_a = scene.analysis_height_m
    for solid in scene.solids:
        _add_solid(acc, spec, solid, z_a, threshold)
    for item in scene.porous:
        _add_porous(acc, spec, item, z_a)
    return Voxels(*acc.finish())
