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
