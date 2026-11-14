"""The study template hash must match the one the comfort endpoints look up."""

from uuid import uuid4

from app.services.comfort.lawson_service import DEFAULT_LAWSON, lawson_hash
from app.services.simulations.aggregate_template import build_template


def test_template_hash_matches_comfort_lookup_hash() -> None:
    """build_template hashes the settings table, like comfort_service and reports."""
    pid = uuid4()
    inputs = {"source": "era5", "id": pid, "cache_key": "era5:k", "z0_m": 1.0,
              "analysis_height_m": 1.5,
              "rose": {"calm_fraction": 0.0, "sectors": [
                  {"center_deg": 0.0, "frequency": 1.0, "weibull_k": 2.0, "weibull_c_ms": 4.0}]}}
    settings = {"lawson": DEFAULT_LAWSON, "turbulence_intensity_default": 0.25}
    t = build_template(inputs, settings, uuid4(), {"frame": "plan"})
    assert t is not None
    assert t["lawson_hash"] == lawson_hash(DEFAULT_LAWSON, 0.25, "era5:k")
    assert t["lawson"]["comfort"][0]["class"] == "A"
