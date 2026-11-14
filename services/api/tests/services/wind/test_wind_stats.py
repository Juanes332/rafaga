"""Wind rose statistics."""

import numpy as np
import pytest

from app.services.wind.wind_stats import build_rose, weibull_fit


def test_sector_assignment_follows_centered_bins() -> None:
    """354 and 6 degrees both fall in the north sector; 11.25 goes to NNE."""
    rose = build_rose([5, 5, 5], [354, 6, 11.25], 1)
    assert rose["sectors"][0]["frequency"] == pytest.approx(2 / 3)
    assert rose["sectors"][1]["frequency"] == pytest.approx(1 / 3)
    assert [s["center_deg"] for s in rose["sectors"]][:3] == [0.0, 22.5, 45.0]


def test_frequencies_and_calm_sum_to_one() -> None:
    """Calm (<0.5 m/s) is excluded from sectors and completes the total."""
    rng = np.random.default_rng(1)
    speed = (rng.weibull(2, 5000) * 4).tolist()
    rose = build_rose(speed, rng.uniform(0, 360, 5000).tolist(), 2)
    total = sum(s["frequency"] for s in rose["sectors"]) + rose["calm_fraction"]
    assert total == pytest.approx(1.0, abs=1e-3) and rose["hours"] == 5000
    assert rose["calm_fraction"] > 0 and rose["period_years"] == 2


def test_weibull_fit_recovers_parameters() -> None:
    """MLE recovers k=2, c=5 from a large sample."""
    sample = np.random.default_rng(3).weibull(2.0, 20000) * 5.0
    k, c = weibull_fit(sample)
    assert k == pytest.approx(2.0, abs=0.1) and c == pytest.approx(5.0, abs=0.15)


def test_percentiles_and_empty_sector() -> None:
    """Order statistics are correct and empty sectors are zeroed."""
    rose = build_rose([1, 2, 3, 4, 5], [0] * 5, 1)
    north, east = rose["sectors"][0], rose["sectors"][4]
    assert north["p50_ms"] == 3 and north["max_ms"] == 5 and north["mean_ms"] == 3
    assert east["frequency"] == 0 and east["max_ms"] == 0


def test_no_valid_hours_raises() -> None:
    """All-NaN input cannot make a rose."""
    with pytest.raises(ValueError):
        build_rose([float("nan")], [1.0], 1)
