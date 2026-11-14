"""Lawson table defaults, hashing and the job-payload form (ADR-15)."""

import copy
import hashlib
import json
from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.comfort.user_settings_reader import read_user_settings

DEFAULT_THRESHOLDS = {"k_accel": 1.2, "k_stagnation": 0.3, "dk_reduction": -0.1}
DEFAULT_TURBULENCE = 0.25
DEFAULT_LAWSON: dict[str, Any] = {
    "exceedance_probability": 0.05,
    "comfort": [
        {"key": "sitting", "label_key": "lawson.sitting", "threshold_ms": 4},
        {"key": "standing", "label_key": "lawson.standing", "threshold_ms": 6},
        {"key": "strolling", "label_key": "lawson.strolling", "threshold_ms": 8},
        {"key": "business_walking", "label_key": "lawson.business_walking", "threshold_ms": 10},
        {"key": "uncomfortable", "label_key": "lawson.uncomfortable", "threshold_ms": None},
    ],
    "safety_probability": 0.00025,
    "safety": [
        {"key": "unsafe_frail", "label_key": "lawson.unsafe_frail", "threshold_ms": 15},
        {"key": "unsafe_all", "label_key": "lawson.unsafe_all", "threshold_ms": 20},
    ],
}


def canonical_json(value: Any) -> str:
    """Serialize with sorted keys and no spaces (job-contract 2.4)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def lawson_hash(lawson: Mapping[str, Any], turbulence: float, rose_cache_key: str | None) -> str:
    """Return the sha256 of {lawson, turbulence_intensity_default, rose_cache_key}."""
    body = {"lawson": lawson, "turbulence_intensity_default": turbulence,
            "rose_cache_key": rose_cache_key}
    return hashlib.sha256(canonical_json(body).encode()).hexdigest()


def lawson_job_payload(lawson: Mapping[str, Any]) -> dict[str, Any]:
    """Convert the settings Lawson table to the aggregate payload form."""
    classes = [c for c in lawson["comfort"] if c["threshold_ms"] is not None]
    letters = "ABCDEFGH"
    return {
        "exceedance": lawson["exceedance_probability"],
        "comfort": [{"class": letters[i], "key": c["key"], "threshold_ms": c["threshold_ms"]}
                    for i, c in enumerate(classes)],
        "uncomfortable_class": letters[len(classes)],
        "safety": [{"key": s["key"], "threshold_ms": s["threshold_ms"],
                    "exceedance": lawson["safety_probability"]} for s in lawson["safety"]],
    }


async def caller_settings(session: AsyncSession, user_id: UUID) -> dict[str, Any]:
    """Return the caller's thresholds, Lawson table and turbulence, with defaults."""
    row = await read_user_settings(session, user_id)
    thresholds = dict(DEFAULT_THRESHOLDS)
    lawson = copy.deepcopy(DEFAULT_LAWSON)
    turbulence = DEFAULT_TURBULENCE
    if row is not None:
        thresholds.update(row["thresholds"] or {})
        lawson = row["lawson"] or lawson
        turbulence = row["turbulence_intensity_default"]
    return {"thresholds": thresholds, "lawson": lawson, "turbulence": turbulence}
