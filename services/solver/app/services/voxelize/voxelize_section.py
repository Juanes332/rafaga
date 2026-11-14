"""Rasterize a scene on a vertical (s, z) section grid (SOL-06, SOL-08)."""

from dataclasses import dataclass

import numpy as np

from app.models.scene.scene_schemas import Scene
from app.services.porous.porous_model import screen_coefficient, vegetation_coefficient
from app.services.voxelize.coverage_service import interval_coverage, line_intervals
from app.services.voxelize.primitive_geometry import (
    footprint, is_vertically_thin, thickened_screen, thin_normal,
)
from app.services.voxelize.voxel_accumulator import VoxelAccumulator
from app.services.voxelize.voxelize_service import Voxels


@dataclass(frozen=True)
class SectionSpec:
    """Section line p0 -> p1 and the (s, z) grid along it."""

    p0: tuple[float, float]
    p1: tuple[float, float]
    s0: float
    dx: float
    ns: int
    nz: int
    samples: int = 4

    @property
    def tangent(self) -> np.ndarray:
        """Return the unit vector from p0 to p1."""
        t = np.subtract(self.p1, self.p0).astype(float)
        return t / np.linalg.norm(t)


def _coverage(spec: SectionSpec, poly, z_min: float, z_max: float) -> np.ndarray | None:
    """Return the (nz, ns) coverage of a prism cut by the section plane."""
    s_end = spec.s0 + spec.ns * spec.dx
    pieces = line_intervals(poly, np.asarray(spec.p0, float), spec.tangent, spec.s0, s_end)
    if not pieces:
        return None
    sc = np.zeros(spec.ns, dtype=np.float32)
    for lo, hi in pieces:
        sc = np.maximum(sc, interval_coverage(lo, hi, spec.s0, spec.dx, spec.ns, spec.samples))
    zc = interval_coverage(z_min, z_max, 0.0, spec.dx, spec.nz, spec.samples)
    return zc[:, None] * sc[None, :]


def _normal(spec: SectionSpec, normal_enu) -> tuple[float, float, float]:
    """Project a horizontal normal on the s axis of the section."""
    along = float(np.dot(normal_enu, spec.tangent))
    return (1.0 if along >= 0 else -1.0, 0.0, 0.0)


def voxelize_section(scene: Scene, spec: SectionSpec, threshold: float = 0.5) -> Voxels:
    """Return mask/pid/table on the (nz, ns) section grid; row 0 = ground."""
    acc = VoxelAccumulator((spec.nz, spec.ns), threshold)
    window = (slice(None), slice(None))
    for solid in scene.solids:
        poly = footprint(solid)
        cov = _coverage(spec, poly, solid.z_min, solid.z_max)
        if cov is None:
            continue
        thin_z = is_vertically_thin(solid, spec.dx, poly)
        normal = (0.0, 1.0, 0.0) if thin_z else _normal(spec, thin_normal(poly))
        acc.add_solid(window, cov, normal)
    for item in scene.porous:
        if item.model == "vegetation":
            cov = _coverage(spec, footprint(item), item.z_min, item.z_max)
            if cov is not None:
                a = vegetation_coefficient(item.drag_coefficient or 0.2, item.lad_m2_m3 or 0.0, spec.dx)
                acc.add_vegetation(window, (a * cov).astype(np.float32))
            continue
        poly, width = thickened_screen(item, spec.dx)
        cov = _coverage(spec, poly, item.z_min, item.z_max)
        if cov is not None:
            a = screen_coefficient(item.loss_coefficient or 0.0, width / spec.dx)
            acc.add_screen(window, (a * cov).astype(np.float32), _normal(spec, item.normal or thin_normal(poly)))
    return Voxels(*acc.finish())
