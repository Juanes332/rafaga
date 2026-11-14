"""Shared types and helpers of the geometry importers."""

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from shapely.geometry import Polygon

UNIT_FACTORS = {"m": 1.0, "cm": 0.01, "mm": 0.001, "ft": 0.3048}
MIN_RING_AREA_M2 = 0.01


class ImporterError(Exception):
    """A file that cannot be read; carries the cause and a fix hint."""

    def __init__(self, cause: str, hint: str) -> None:
        """Store the cause and the suggested fix."""
        super().__init__(cause)
        self.cause, self.hint = cause, hint


@dataclass
class ImportResult:
    """Buildings in file units plus what was skipped."""

    buildings: list[dict[str, Any]] = field(default_factory=list)
    ignored: list[dict[str, str]] = field(default_factory=list)
    detected_unit: str = "unknown"
    warnings: list[str] = field(default_factory=list)
    metric: bool = False


def new_building(
    name: str, ring: list[list[float]], height: float | None, source: str,
    tiers: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a building dict with a fresh uuid, in file units."""
    building: dict[str, Any] = {
        "id": str(uuid4()), "name": name[:80], "footprint": ring, "holes": [],
        "height_m": height, "source": source, "missing_height": height is None,
    }
    if tiers:
        building["tiers"] = tiers
    return building


def scale_building(b: dict[str, Any], k: float) -> None:
    """Scale every coordinate and height of a building by k, in place."""
    def ring(r: list[list[float]]) -> list[list[float]]:
        return [[x * k, y * k] for x, y in r]

    b["footprint"] = ring(b["footprint"])
    if b["height_m"] is not None:
        b["height_m"] *= k
    for tier in b.get("tiers", []):
        tier["footprint"] = ring(tier["footprint"])
        tier["z_from"] *= k
        tier["z_to"] *= k


def translate_building(b: dict[str, Any], dx: float, dy: float) -> None:
    """Shift every footprint of a building by (dx, dy), in place."""
    def ring(r: list[list[float]]) -> list[list[float]]:
        return [[x + dx, y + dy] for x, y in r]

    b["footprint"] = ring(b["footprint"])
    for tier in b.get("tiers", []):
        tier["footprint"] = ring(tier["footprint"])


def bounds_center(buildings: list[dict[str, Any]]) -> tuple[float, float]:
    """Return the centre of the joint bounding box of the footprints."""
    xs = [p[0] for b in buildings for p in b["footprint"]]
    ys = [p[1] for b in buildings for p in b["footprint"]]
    return (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2


def ring_area(ring: list[list[float]]) -> float:
    """Return the absolute area of a ring."""
    return Polygon(ring).area
