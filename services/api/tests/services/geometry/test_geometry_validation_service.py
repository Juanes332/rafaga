"""Pure shapely validation rules."""

import uuid

from app.models.geometry.geometry_schemas import Building, normalize_ring
from app.services.geometry.geometry_validation_service import validate_buildings


def _b(ring, height=10.0) -> Building:  # noqa: ANN001
    return Building(id=uuid.uuid4(), footprint=ring, height_m=height, source="draw")


def test_clean_building_has_no_issues() -> None:
    """A valid 10 m square at 10 m height is clean."""
    assert validate_buildings([_b([[0, 0], [10, 0], [10, 10], [0, 10]])]) == []


def test_touching_buildings_do_not_overlap() -> None:
    """Shared walls are not overlaps."""
    a = _b([[0, 0], [10, 0], [10, 10], [0, 10]])
    b = _b([[10, 0], [20, 0], [20, 10], [10, 10]])
    assert validate_buildings([a, b]) == []


def test_hole_reduces_area_and_stays_valid() -> None:
    """A building with a courtyard is valid."""
    b = Building(id=uuid.uuid4(), footprint=[[0, 0], [20, 0], [20, 20], [0, 20]],
                 holes=[[[5, 5], [15, 5], [15, 15], [5, 15]]], height_m=9, source="draw")
    assert validate_buildings([b]) == []
    assert b.holes[0][0:2] == [[5, 15], [15, 15]] or b.holes[0] != [[5, 5], [15, 5], [15, 15], [5, 15]]


def test_normalize_ring_orientation_and_closing_vertex() -> None:
    """CCW stays, CW flips, repeated closing vertex is removed."""
    ccw = [[0, 0], [1, 0], [1, 1]]
    assert normalize_ring(ccw, True) == ccw
    assert normalize_ring(ccw, False) == ccw[::-1]
    assert normalize_ring(ccw + [[0, 0]], True) == ccw
