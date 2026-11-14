"""Shapely geometry of scene primitives and their thin-axis normals."""

import numpy as np
from shapely import affinity
from shapely.geometry import Polygon
from shapely.ops import unary_union

from app.models.scene.scene_schemas import Porous, Prism


def footprint(prism: Prism) -> Polygon:
    """Return the prism footprint (with holes) as a valid polygon."""
    poly = Polygon(prism.footprint, [h for h in prism.holes if len(h) >= 3])
    return poly if poly.is_valid else poly.buffer(0)


def thin_normal(poly: Polygon) -> np.ndarray:
    """Return the unit ENU normal of the polygon's largest face."""
    rect = np.asarray(poly.minimum_rotated_rectangle.exterior.coords)[:4]
    e1, e2 = rect[1] - rect[0], rect[2] - rect[1]
    short = e1 if np.linalg.norm(e1) < np.linalg.norm(e2) else e2
    length = np.linalg.norm(short)
    return short / length if length > 0 else np.array([1.0, 0.0])


def thin_width(poly: Polygon) -> float:
    """Return the smallest side of the minimum rotated rectangle."""
    rect = np.asarray(poly.minimum_rotated_rectangle.exterior.coords)[:4]
    return float(min(np.linalg.norm(rect[1] - rect[0]), np.linalg.norm(rect[2] - rect[1])))


def thickened_screen(screen: Porous, dx_m: float, side: int = 0) -> tuple[Polygon, float]:
    """Return the screen band widened to max(dx, thickness) and that width.

    side 0 widens symmetrically; +1 / -1 widen only toward +normal /
    -normal, which keeps a screen next to a wall out of the wall cells.
    """
    poly = footprint(screen)
    thickness = screen.thickness_m or thin_width(poly)
    width = max(dx_m, thickness)
    normal = np.asarray(screen.normal or thin_normal(poly), dtype=float)
    extra = width - thickness
    if extra <= 0:
        return poly, width
    shifts = (-0.5 * extra, 0.5 * extra) if side == 0 else (0.0, side * extra)
    moved = [affinity.translate(poly, *(s * normal)) for s in shifts]
    return unary_union([poly, *moved]).convex_hull, width


def is_vertically_thin(prism: Prism, dx_m: float, poly: Polygon) -> bool:
    """Return True when the prism is thinner in z than in plan and than dx."""
    dz = prism.z_max - prism.z_min
    return dz < dx_m and dz < thin_width(poly)
