"""STL/OBJ importer: one building per body, stacked 3 m tiers (ADR-24)."""

import io
from typing import Any

import numpy as np
import trimesh
from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry

from app.services.geometry.importers.importer_common import (
    ImporterError,
    ImportResult,
    new_building,
)

TIER_HEIGHT_M = 3.0
SAME_AREA_RATIO = 0.01


def _largest(geom: BaseGeometry) -> Polygon | None:
    """Return the biggest polygon of a shapely result."""
    if isinstance(geom, Polygon):
        return geom if not geom.is_empty else None
    if isinstance(geom, MultiPolygon) and not geom.is_empty:
        return max(geom.geoms, key=lambda g: g.area)
    return None


def _slice_polygon(body: trimesh.Trimesh, z: float) -> Polygon | None:
    """Return the horizontal section polygon at height z, or the hull."""
    section = body.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    result: BaseGeometry = Polygon()
    if section is not None:
        for ring in section.discrete:
            if len(ring) >= 4:
                result = result.symmetric_difference(Polygon(ring[:, :2]).buffer(0))
    poly = _largest(result)
    if poly is None:
        poly = _largest(Polygon(body.convex_hull.vertices[:, :2]).convex_hull)
    return poly


def _ring(poly: Polygon) -> list[list[float]]:
    """Return the exterior ring without the closing vertex."""
    clean = poly.simplify(1e-6)
    return [[float(x), float(y)] for x, y in list(clean.exterior.coords)[:-1]]


def _tiers(body: trimesh.Trimesh, height: float) -> list[dict[str, Any]]:
    """Slice a body every 3 m and merge identical consecutive tiers."""
    tiers: list[dict[str, Any]] = []
    z0 = 0.0
    zmin = float(body.bounds[0][2])
    while z0 < height - 1e-6:
        z1 = min(z0 + TIER_HEIGHT_M, height)
        poly = _slice_polygon(body, zmin + (z0 + z1) / 2)
        if poly is not None:
            last = tiers[-1] if tiers else None
            same = last and abs(last["_area"] - poly.area) <= SAME_AREA_RATIO * poly.area
            if same:
                last["z_to"] = z1
            else:
                tiers.append({"z_from": z0, "z_to": z1, "footprint": _ring(poly),
                              "_area": poly.area})
        z0 = z1
    for tier in tiers:
        del tier["_area"]
    return tiers


def read_mesh(data: bytes, extension: str, stem: str) -> ImportResult:
    """Parse an STL or OBJ file into building tiers in file units."""
    try:
        mesh = trimesh.load(io.BytesIO(data), file_type=extension, force="mesh")
        bodies = mesh.split(only_watertight=False)
    except Exception as exc:  # noqa: BLE001 - trimesh raises many types
        raise ImporterError(
            "The mesh could not be parsed.", "Export it again as a valid STL or OBJ."
        ) from exc
    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.faces) == 0:
        raise ImporterError("The file holds no triangles.", "Check the export options.")
    result = ImportResult(detected_unit="unknown")
    for n, body in enumerate(bodies, 1):
        height = float(np.ptp(body.bounds[:, 2]))
        tiers = _tiers(body, height) if height > 0 else []
        if not tiers:
            result.ignored.append({"entity": f"body#{n}", "reason": "flat_body"})
            continue
        footprint = tiers[0]["footprint"]
        result.buildings.append(new_building(
            f"{stem} {n}", footprint, height, extension,
            tiers if len(tiers) > 1 else None))
    return result
