"""Cell coverage of polygons and intervals on regular grids (ADR-13).

Coverage is the exact covered fraction quantized to the supersampling
resolution (1/s^2 in plan, 1/s per axis), with any non-zero overlap
kept at one sample at least: an element thinner than the sample
spacing still blocks flow instead of vanishing between samples.
"""

from dataclasses import dataclass

import numpy as np
import shapely
from shapely.geometry import LineString, Polygon


@dataclass(frozen=True)
class AxisGrid:
    """Regular axis-aligned 2D grid of square cells."""

    x0: float
    y0: float
    dx: float
    nx: int
    ny: int


def quantize(coverage: np.ndarray, levels: int) -> np.ndarray:
    """Round coverage to 1/levels keeping tiny overlaps at one level."""
    q = np.round(coverage * levels) / levels
    q = np.where((coverage > 1e-9) & (q == 0), 1.0 / levels, q)
    return np.clip(q, 0.0, 1.0).astype(np.float32)


def polygon_coverage(poly: Polygon, grid: AxisGrid, samples: int) -> tuple[tuple[slice, slice], np.ndarray]:
    """Return the (rows, cols) window and the coverage of poly inside it."""
    xmin, ymin, xmax, ymax = poly.bounds
    i0 = max(int(np.floor((xmin - grid.x0) / grid.dx)), 0)
    i1 = min(int(np.ceil((xmax - grid.x0) / grid.dx)), grid.nx)
    j0 = max(int(np.floor((ymin - grid.y0) / grid.dx)), 0)
    j1 = min(int(np.ceil((ymax - grid.y0) / grid.dx)), grid.ny)
    window = (slice(j0, max(j1, j0)), slice(i0, max(i1, i0)))
    if i1 <= i0 or j1 <= j0:
        return window, np.zeros((0, 0), dtype=np.float32)
    ii, jj = np.meshgrid(np.arange(i0, i1), np.arange(j0, j1))
    x = grid.x0 + ii * grid.dx
    y = grid.y0 + jj * grid.dx
    boxes = shapely.box(x, y, x + grid.dx, y + grid.dx)
    area = shapely.area(shapely.intersection(boxes, poly)) / grid.dx**2
    return window, quantize(area, samples * samples)


def interval_coverage(lo: float, hi: float, start: float, dx: float, n: int, samples: int) -> np.ndarray:
    """Return the per-cell covered fraction of [lo, hi] on a 1D grid."""
    edges = start + np.arange(n + 1) * dx
    overlap = np.clip(np.minimum(edges[1:], hi) - np.maximum(edges[:-1], lo), 0.0, None)
    return quantize(overlap / dx, samples)


def line_intervals(poly: Polygon, origin: np.ndarray, tangent: np.ndarray, s0: float, s1: float) -> list[tuple[float, float]]:
    """Return [s_a, s_b] pieces where the line origin + s t is inside poly."""
    line = LineString([origin + s0 * tangent, origin + s1 * tangent])
    cut = line.intersection(poly)
    parts = getattr(cut, "geoms", [cut])
    out = []
    for part in parts:
        if part.is_empty or part.length == 0:
            continue
        pts = np.asarray(part.coords)
        s = (pts - origin) @ tangent
        out.append((float(s.min()), float(s.max())))
    return out
