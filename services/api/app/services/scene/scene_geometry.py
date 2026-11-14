"""Planar helpers for the scene compiler: rings, edges, offsets."""

import math
from typing import Any

from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

Point = tuple[float, float]
Frame = tuple[Point, Point, Point, float]


def round_point(p: Point) -> list[float]:
    """Round a point to micrometres for stable JSON."""
    return [round(float(p[0]), 6), round(float(p[1]), 6)]


def ring_ccw(points: list[Point]) -> list[list[float]]:
    """Return an open, counter-clockwise ring."""
    poly = orient(Polygon(points), 1.0)
    return [round_point(p) for p in list(poly.exterior.coords)[:-1]]


def polygon_rings(footprint: list[Any], holes: list[Any]) -> tuple[list[list[float]], list[list[list[float]]]]:
    """Return an outer ring (CCW) and hole rings (CW), closing vertex dropped."""
    poly = orient(Polygon(footprint, holes), 1.0)
    outer = [round_point(p) for p in list(poly.exterior.coords)[:-1]]
    inner = [[round_point(p) for p in list(r.coords)[:-1]] for r in poly.interiors]
    return outer, inner


def edge_frame(footprint: list[Any], index: int) -> tuple[Point, Point, Point, float] | None:
    """Return start, unit direction, outward unit normal and length of an edge.

    Edge i runs from vertex i to vertex i+1 as stored. For a CCW ring
    the outward normal is the direction rotated -90 degrees; a CW
    ring flips it. Returns None for a missing or zero-length edge.
    """
    if not 0 <= index < len(footprint):
        return None
    a = (float(footprint[index][0]), float(footprint[index][1]))
    nxt = footprint[(index + 1) % len(footprint)]
    b = (float(nxt[0]), float(nxt[1]))
    length = math.dist(a, b)
    if length < 1e-6:
        return None
    ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
    sign = 1.0 if Polygon(footprint).exterior.is_ccw else -1.0
    return a, (ux, uy), (sign * uy, -sign * ux), length


def edge_rectangle(
    a: Point, u: Point, n: Point, t0: float, t1: float, d0: float, d1: float
) -> list[list[float]]:
    """Return the CCW rectangle spanning t0..t1 along and d0..d1 outward."""
    def at(t: float, d: float) -> Point:
        return (a[0] + u[0] * t + n[0] * d, a[1] + u[1] * t + n[1] * d)

    return ring_ccw([at(t0, d0), at(t1, d0), at(t1, d1), at(t0, d1)])


def cut_inward(poly: Polygon, a: Point, n: Point, distance: float) -> Polygon | None:
    """Remove the strip within `distance` of an edge line, inward side kept.

    Returns None when what remains is empty or smaller than 1 m2.
    """
    far = 1e5
    px, py = -n[1], n[0]
    cx, cy = a[0] - n[0] * distance, a[1] - n[1] * distance
    keep = Polygon([
        (cx + px * far, cy + py * far), (cx - px * far, cy - py * far),
        (cx - px * far - n[0] * far, cy - py * far - n[1] * far),
        (cx + px * far - n[0] * far, cy + py * far - n[1] * far),
    ])
    result = poly.intersection(keep)
    if result.is_empty:
        return None
    if result.geom_type != "Polygon":
        parts = [g for g in getattr(result, "geoms", []) if g.geom_type == "Polygon"]
        if not parts:
            return None
        result = max(parts, key=lambda g: g.area)
    return result if result.is_valid and result.area >= 1.0 else None
