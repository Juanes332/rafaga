"""Zone area maths."""

import numpy as np

from app.services.results.zone_calculator import compute_zones, fluid_area, reduction_zone


def test_nan_cells_are_not_fluid() -> None:
    """Solid cells are excluded from the fluid area."""
    k = np.array([[1.0, np.nan]])
    assert fluid_area(k, 2.0) == 4.0


def test_zero_fluid_does_not_divide_by_zero() -> None:
    """An all-solid field yields zero percentages."""
    zones = compute_zones(np.array([[np.nan]]), 1.0, 1.2, 0.3)
    assert [z["percent"] for z in zones] == [0.0, 0.0]


def test_reduction_counts_cells_below_dk() -> None:
    """Only cells whose delta is below dk count."""
    z = reduction_zone(np.array([[1.0, 1.0]]), np.array([[0.8, 0.95]]), 1.0, -0.1)
    assert z["area_m2"] == 1.0 and z["percent"] == 50.0
