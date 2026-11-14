"""Geometry validation with shapely (BR-14)."""

from shapely import STRtree
from shapely.geometry import Polygon

from app.models.geometry.geometry_schemas import Building, GeometryIssue

MIN_FOOTPRINT_M2 = 1.0
MIN_HEIGHT_M, MAX_HEIGHT_M = 1.0, 500.0
OVERLAP_TOLERANCE_M2 = 0.01


def _issue(b: Building, code: str, at: list[float] | None = None) -> GeometryIssue:
    """Build an issue with its i18n key and a default location."""
    return GeometryIssue(
        building_id=b.id, code=code, message_key=f"geometry.issue.{code}",
        location=at or b.footprint[0],
    )


def _shape_issue(b: Building, poly: Polygon) -> GeometryIssue | None:
    """Return the shape issue of one building, if any."""
    if len({tuple(p) for p in b.footprint}) < 3:
        return _issue(b, "not_closed")
    if not poly.is_valid:
        return _issue(b, "self_intersection")
    if poly.area < MIN_FOOTPRINT_M2:
        return _issue(b, "footprint_too_small")
    return None


def _height_issue(b: Building) -> GeometryIssue | None:
    """Return the height issue of one building, if any."""
    if b.height_m is None:
        return _issue(b, "missing_height")
    if not MIN_HEIGHT_M <= b.height_m <= MAX_HEIGHT_M:
        return _issue(b, "height_out_of_range")
    return None


def _overlaps(buildings: list[Building], polys: list[Polygon | None]) -> list[GeometryIssue]:
    """Return one overlap issue per later building of every overlapping pair."""
    valid = [(i, p) for i, p in enumerate(polys) if p is not None]
    if len(valid) < 2:
        return []
    tree = STRtree([p for _, p in valid])
    found: dict[int, GeometryIssue] = {}
    for a, (i, pa) in enumerate(valid):
        for k in tree.query(pa):
            j, pb = valid[int(k)]
            if j <= i:
                continue
            common = pa.intersection(pb)
            if common.area > OVERLAP_TOLERANCE_M2 and j not in found:
                point = common.representative_point()
                found[j] = _issue(buildings[j], "overlap", [point.x, point.y])
    return list(found.values())


def validate_buildings(buildings: list[Building]) -> list[GeometryIssue]:
    """Return every geometry issue of a building set."""
    issues: list[GeometryIssue] = []
    polys: list[Polygon | None] = []
    for b in buildings:
        poly = Polygon(b.footprint, b.holes)
        problem = _shape_issue(b, poly)
        polys.append(None if problem else poly)
        issues.extend(i for i in (problem, _height_issue(b)) if i)
    return issues + _overlaps(buildings, polys)
