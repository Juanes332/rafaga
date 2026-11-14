"""Lawson helpers shared with the simulations domain."""

from app.services.comfort.lawson_service import (
    DEFAULT_LAWSON,
    canonical_json,
    lawson_hash,
    lawson_job_payload,
)


def test_canonical_json_is_sorted_and_compact() -> None:
    """Key order and spacing never change the hash."""
    assert canonical_json({"b": 1, "a": [1, 2]}) == '{"a":[1,2],"b":1}'


def test_hash_depends_on_every_input() -> None:
    """Lawson, turbulence and rose key all matter."""
    base = lawson_hash(DEFAULT_LAWSON, 0.25, "k")
    assert len(base) == 64
    assert base != lawson_hash(DEFAULT_LAWSON, 0.3, "k")
    assert base != lawson_hash(DEFAULT_LAWSON, 0.25, "other")
    assert base == lawson_hash(dict(reversed(list(DEFAULT_LAWSON.items()))), 0.25, "k")


def test_job_payload_form_matches_the_contract() -> None:
    """Classes A..D, uncomfortable E and per-item safety exceedance."""
    p = lawson_job_payload(DEFAULT_LAWSON)
    assert [c["class"] for c in p["comfort"]] == ["A", "B", "C", "D"]
    assert p["uncomfortable_class"] == "E" and p["exceedance"] == 0.05
    assert p["safety"][0] == {"key": "unsafe_frail", "threshold_ms": 15, "exceedance": 0.00025}
