"""Expand base buildings (and setback stacks) into solid prisms."""

import math
from typing import Any

from shapely.geometry import Polygon

from app.services.scene.scene_geometry import (
    Frame,
    cut_inward,
    polygon_rings,
    round_point,
)

EPS = 1e-9


def building_height(building: dict[str, Any]) -> float | None:
    """Return the building height, falling back to its tallest tier."""
    if building.get("height_m"):
        return float(building["height_m"])
    tiers = building.get("tiers") or []
    return max((t["z_to"] for t in tiers), default=None)


def _solid(bid: str, tag: str, kind: str, outer: Any, holes: Any, z0: float, z1: float) -> dict[str, Any]:
    """Build one building-derived solid."""
    return {
        "id": f"b:{bid}:{tag}", "origin": {"kind": kind, "building_id": bid, "element_id": None},
        "footprint": outer, "holes": holes, "z_min": round(z0, 6), "z_max": round(z1, 6),
        "thin_axis_m": None,
    }


def _plain(building: dict[str, Any], height: float) -> list[dict[str, Any]]:
    """Return one solid per tier, or a single solid without tiers."""
    bid = building["id"]
    tiers = building.get("tiers") or []
    if not tiers:
        outer, holes = polygon_rings(building["footprint"], building.get("holes") or [])
        return [_solid(bid, "t0", "building", outer, holes, 0.0, height)]
    out = []
    for k, t in enumerate(tiers):
        outer, holes = polygon_rings(t["footprint"], [])
        out.append(_solid(bid, f"t{k}", "building_tier", outer, holes, t["z_from"], t["z_to"]))
    return out


def _breakpoints(setbacks: list[tuple[dict[str, Any], Frame]], height: float) -> list[float]:
    """Return the sorted elevations where a setback level begins."""
    points = {0.0, height}
    for el, _ in setbacks:
        p = el["params"]
        z, step = p["start_floor"] * p["floor_height_m"], p["floor_height_m"]
        while z < height - EPS:
            points.add(round(z, 6))
            z += step
    return sorted(points)


def _offset_at(el: dict[str, Any], z: float) -> float:
    """Return the inward offset of a setback element at elevation z."""
    p = el["params"]
    start = p["start_floor"] * p["floor_height_m"]
    if z < start - EPS:
        return 0.0
    return p["setback_m"] * (math.floor((z - start) / p["floor_height_m"] + EPS) + 1)


def _tier_polygon(base: Polygon, setbacks: list[tuple[dict[str, Any], Frame]], z: float) -> tuple[Polygon | None, str | None]:
    """Cut every active setback; return the polygon or the failing element id."""
    poly: Polygon | None = base
    for el, frame in setbacks:
        d = _offset_at(el, z)
        if d > 0:
            poly = cut_inward(poly, frame[0], frame[2], d)
            if poly is None:
                return None, el["id"]
    return poly, None


def _setback_stack(building: dict[str, Any], height: float, setbacks: list[tuple[dict[str, Any], Frame]], warnings: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Stack tiers between setback levels; truncate when one degenerates."""
    base = Polygon(building["footprint"], building.get("holes") or [])
    marks = _breakpoints(setbacks, height)
    solids: list[dict[str, Any]] = []
    for k, (z0, z1) in enumerate(zip(marks, marks[1:])):
        poly, failed = _tier_polygon(base, setbacks, z0)
        if poly is None:
            warnings.append({"code": "setback_tiers_truncated", "ref": failed or ""})
            # Keep the envelope conservative: the last valid tier runs up.
            solids[-1]["z_max"] = round(height, 6)
            break
        outer, holes = polygon_rings(list(poly.exterior.coords)[:-1], [list(r.coords)[:-1] for r in poly.interiors])
        solids.append(_solid(building["id"], f"s{k}", "setback_tier", outer, holes, z0, z1))
    return solids


def building_solids(building: dict[str, Any], height: float, setbacks: list[tuple[dict[str, Any], Frame]], warnings: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Return the solids of one building, honouring setback elements."""
    if not setbacks:
        return _plain(building, height)
    return _setback_stack(building, height, setbacks, warnings)


def building_extent(building: dict[str, Any]) -> list[list[float]]:
    """Return every outer vertex of a building, tiers included."""
    rings = [building["footprint"]] + [t["footprint"] for t in building.get("tiers") or []]
    return [round_point((p[0], p[1])) for ring in rings for p in ring]
