"""Recorded-style Open-Meteo fixtures for the geo tests."""

import json
from pathlib import Path

import pytest
import respx

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def load(name: str) -> dict:
    """Load a JSON fixture."""
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def mocked() -> respx.MockRouter:
    """Return a respx router that rejects any unmocked outbound call."""
    with respx.mock(assert_all_called=False) as router:
        yield router


def synthetic_hourly(hours: int = 8760) -> dict:
    """Return deterministic hourly ERA5-style data (synthetic site)."""
    import numpy as np

    rng = np.random.default_rng(7)
    direction = np.where(rng.random(hours) < 0.6, rng.normal(270, 20, hours), rng.uniform(0, 360, hours)) % 360
    speed = rng.weibull(2.0, hours) * 4.5
    speed[:50] = 0.2
    return {"hourly": {"time": ["t"] * hours,
                       "wind_speed_10m": [round(float(s), 2) for s in speed],
                       "wind_direction_10m": [round(float(d), 1) for d in direction]}}
