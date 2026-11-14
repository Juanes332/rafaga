"""Minimal geometry gate before a simulation is queued."""

from collections.abc import Sequence
from typing import Any

from shapely.geometry import Polygon

from app.core.errors.simulation_errors import GeometryInvalidError


def geometry_issues(buildings: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return blocking issues of the stored base buildings."""
    if not buildings:
        return [{"building_id": None, "code": "no_buildings"}]
    issues = []
    for b in buildings:
        if b.get("height_m") is None:
            issues.append({"building_id": b.get("id"), "code": "missing_height"})
        if not Polygon(b["footprint"]).is_valid:
            issues.append({"building_id": b.get("id"), "code": "self_intersection"})
    return issues


def ensure_simulable(buildings: Sequence[dict[str, Any]]) -> None:
    """Raise GeometryInvalidError when any blocking issue exists."""
    issues = geometry_issues(buildings)
    if issues:
        raise GeometryInvalidError(details={"issues": issues})
