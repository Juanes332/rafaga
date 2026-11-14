"""Compile base buildings and facade elements into the canonical scene."""

from datetime import UTC, datetime
from typing import Any

from app.services.facades.facade_strategies_catalogue import clamp_params
from app.services.scene.scene_buildings import (
    building_extent,
    building_height,
    building_solids,
)
from app.services.scene.scene_facades import expand_element
from app.services.scene.scene_geometry import edge_frame

SCHEMA_VERSION = "1.0"


def _bounds(buildings: list[dict[str, Any]], h_max: float, envelope_m: float) -> dict[str, Any]:
    """Return the base bounds block."""
    pts = [p for b in buildings for p in building_extent(b)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return {
        "base_min": [min(xs), min(ys), 0.0], "base_max": [max(xs), max(ys), h_max],
        "envelope_m": int(envelope_m),
    }


def _classify(
    elements: list[dict[str, Any]], by_id: dict[str, dict[str, Any]], warnings: list[dict[str, str]]
) -> dict[str, list[tuple[dict[str, Any], Any]]]:
    """Group usable elements by building; orphans and degenerates warn."""
    grouped: dict[str, list[tuple[dict[str, Any], Any]]] = {}
    for el in elements:
        building = by_id.get(str(el["building_id"]))
        n = len(building["footprint"]) if building else 0
        if building is None or not 0 <= el["edge_index"] < n:
            warnings.append({"code": "element_orphaned", "ref": str(el["id"])})
            continue
        frame = edge_frame(building["footprint"], el["edge_index"])
        if frame is None:
            warnings.append({"code": "element_degenerate", "ref": str(el["id"])})
            continue
        # Defaults are re-applied so a sparse stored element still compiles.
        params, _ = clamp_params(el["type"], el.get("params") or {})
        item = {**el, "params": params, "id": str(el["id"]), "building_id": str(el["building_id"])}
        grouped.setdefault(str(building["id"]), []).append((item, frame))
    return grouped


def compile_scene(
    *, project_id: str, alternative_id: str, geometry_version: int,
    buildings: list[dict[str, Any]], elements: list[dict[str, Any]],
    z0_m: float, analysis_height_m: float, vegetation_cd: float,
    envelope_m: float, compiled_at: datetime | None = None,
) -> dict[str, Any]:
    """Return the canonical scene dict (contracts/scene.schema.json)."""
    usable = [b for b in buildings if building_height(b) is not None]
    by_id = {str(b["id"]): b for b in usable}
    warnings: list[dict[str, str]] = []
    grouped = _classify(elements, by_id, warnings)
    solids: list[dict[str, Any]] = []
    porous: list[dict[str, Any]] = []
    for b in usable:
        height = building_height(b)
        items = grouped.get(str(b["id"]), [])
        setbacks = [i for i in items if i[0]["type"] == "setback"]
        solids += building_solids(b, height, setbacks, warnings)
        for el, frame in (i for i in items if i[0]["type"] != "setback"):
            s, p, w = expand_element(el, frame, height, analysis_height_m, vegetation_cd)
            solids += s
            porous += p
            warnings += w
    h_max = max(building_height(b) for b in usable)
    stamp = (compiled_at or datetime.now(UTC)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema_version": SCHEMA_VERSION, "units": "m", "frame": "local_enu",
        "source": {"project_id": project_id, "alternative_id": alternative_id,
                   "geometry_version": geometry_version, "compiled_at": stamp},
        "analysis_height_m": analysis_height_m, "ground": {"z0_m": z0_m},
        "h_max_m": h_max, "bounds": _bounds(usable, h_max, envelope_m),
        "solids": solids, "porous": porous, "warnings": warnings,
    }
