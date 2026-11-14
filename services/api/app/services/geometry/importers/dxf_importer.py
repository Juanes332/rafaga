"""DXF importer: closed polylines become buildings (ADR-24)."""

import io
import re
from typing import Any

import ezdxf
from ezdxf.lldxf.const import DXFError

from app.services.geometry.importers.importer_common import (
    MIN_RING_AREA_M2,
    ImporterError,
    ImportResult,
    new_building,
    ring_area,
)

INSUNITS = {1: "ft", 2: "ft", 4: "mm", 5: "cm", 6: "m"}
_NUMBER = re.compile(r"-?\d+(?:[.,]\d+)?")


def _layer_height(layer: str) -> float | None:
    """Read a height from a layer name such as 'H12.5' or 'building_30'."""
    found = _NUMBER.findall(layer)
    return float(found[-1].replace(",", ".")) if found else None


def _xdata_height(entity: Any) -> float | None:
    """Read a 'height' value from XDATA or an attribute-like dict."""
    if entity.has_xdata("RAFAGA"):
        for code, value in entity.get_xdata("RAFAGA"):
            if code == 1040 or code == 1070:
                return float(value)
    return None


def _entity_height(entity: Any) -> float | None:
    """Return the height of an entity from XDATA first, then its layer."""
    return _xdata_height(entity) or _layer_height(entity.dxf.layer)


def _ring(entity: Any) -> list[list[float]] | None:
    """Return the vertices of a closed polyline, or None when open."""
    if entity.dxftype() == "LWPOLYLINE":
        pts = [[p[0], p[1]] for p in entity.get_points("xy")]
    else:
        pts = [[v.dxf.location.x, v.dxf.location.y] for v in entity.vertices]
    return pts if entity.is_closed and len(pts) >= 3 else None


def read_dxf(data: bytes) -> ImportResult:
    """Parse a DXF file into buildings expressed in file units."""
    try:
        doc = ezdxf.read(io.StringIO(data.decode("utf-8", errors="replace")))
    except (DXFError, OSError, ValueError) as exc:
        raise ImporterError(
            "The DXF structure is corrupt.", "Re-export the drawing as ASCII DXF."
        ) from exc
    result = ImportResult(
        detected_unit=INSUNITS.get(doc.header.get("$INSUNITS", 0), "unknown")
    )
    for n, entity in enumerate(doc.modelspace().query("LWPOLYLINE POLYLINE"), 1):
        ring = _ring(entity)
        label = f"{entity.dxftype()}#{entity.dxf.handle}"
        if ring is None:
            result.ignored.append({"entity": label, "reason": "open_polyline"})
        elif ring_area(ring) < MIN_RING_AREA_M2 * 1e-6:
            result.ignored.append({"entity": label, "reason": "degenerate_polygon"})
        else:
            height = _entity_height(entity)
            result.buildings.append(
                new_building(f"{entity.dxf.layer} {n}", ring, height, "dxf")
            )
    return result
