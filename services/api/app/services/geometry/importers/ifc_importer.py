"""IFC importer: axis-aligned boxes of building elements (ADR-24, R2)."""

import tempfile
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element as element_util
import ifcopenshell.util.unit as unit_util
import numpy as np

from app.services.geometry.importers.importer_common import (
    ImporterError,
    ImportResult,
    new_building,
)

_UNITS = {1.0: "m", 0.01: "cm", 0.001: "mm", 0.3048: "ft"}


def _open(data: bytes) -> ifcopenshell.file:
    """Open IFC bytes through a temporary file."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "model.ifc"
        path.write_bytes(data)
        try:
            return ifcopenshell.open(str(path))
        except Exception as exc:  # noqa: BLE001 - ifcopenshell raises many types
            raise ImporterError(
                "The IFC file could not be parsed.", "Export it again as IFC2x3 or IFC4."
            ) from exc


def _bbox(elements: list, settings: ifcopenshell.geom.settings) -> np.ndarray | None:
    """Return the joint (min, max) bounding box of element geometry."""
    points = []
    for el in elements:
        try:
            shape = ifcopenshell.geom.create_shape(settings, el)
        except Exception:  # noqa: BLE001 - elements without geometry are skipped
            continue
        points.append(np.array(shape.geometry.verts).reshape(-1, 3))
    return np.vstack(points) if points else None


def _building_elements(model: ifcopenshell.file, building) -> list:
    """Return the physical elements contained in a building."""
    found = [e for e in element_util.get_decomposition(building)
             if e.is_a("IfcBuildingElement")]
    if not found:
        found = [e for e in element_util.get_decomposition(building, is_recursive=True)
                 if e.is_a("IfcBuildingElement")]
    return found


def read_ifc(data: bytes) -> ImportResult:
    """Parse an IFC file into one box-shaped building per IfcBuilding."""
    model = _open(data)
    scale = unit_util.calculate_unit_scale(model)
    result = ImportResult(detected_unit=_UNITS.get(round(scale, 4), "unknown"))
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)
    for n, building in enumerate(model.by_type("IfcBuilding"), 1):
        box = _bbox(_building_elements(model, building), settings)
        if box is None:
            result.ignored.append({"entity": f"IfcBuilding#{n}", "reason": "no_geometry"})
            continue
        (x0, y0, z0), (x1, y1, z1) = box.min(axis=0), box.max(axis=0)
        x0, y0, x1, y1 = float(x0), float(y0), float(x1), float(y1)
        ring = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
        result.buildings.append(
            new_building(building.Name or f"IfcBuilding {n}", ring, float(z1 - z0), "ifc"))
    # ifcopenshell returns world coordinates in metres whatever the file unit.
    result.metric = True
    return result
