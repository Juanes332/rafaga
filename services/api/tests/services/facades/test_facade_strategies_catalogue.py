"""Catalogue of facade strategies: ranges, defaults, clamping."""

import pytest

from app.core.errors.alternative_errors import InvalidFacadeParamsError
from app.services.facades.facade_strategies_catalogue import STRATEGIES, clamp_params


def test_catalogue_matches_plan_ranges() -> None:
    """Spot-check ranges and defaults from the developer spec."""
    spec = {p["key"]: p for p in STRATEGIES["vegetation"]}
    assert (spec["lad_m2_m3"]["min"], spec["lad_m2_m3"]["max"], spec["lad_m2_m3"]["default"]) == (0.1, 5.0, 1.0)
    assert {p["key"] for p in STRATEGIES["canopy"]} == {"overhang_m", "height_m", "thickness_m"}


def test_clamp_reports_each_adjustment() -> None:
    """Values below min and above max are clamped with reasons."""
    params, adj = clamp_params("fins", {"depth_m": 0.0, "pitch_m": 50})
    assert params["depth_m"] == 0.1 and params["pitch_m"] == 10 and params["height_m"] is None
    assert {a["field"] for a in adj} == {"depth_m", "pitch_m"}


def test_integer_parameter_is_rounded() -> None:
    """start_floor stays an integer."""
    params, adj = clamp_params("setback", {"start_floor": 2.6})
    assert params["start_floor"] == 3 and adj == []


def test_non_numeric_value_is_rejected() -> None:
    """Strings are not parameters."""
    with pytest.raises(InvalidFacadeParamsError):
        clamp_params("screen", {"porosity": "high"})
