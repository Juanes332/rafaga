"""The aggregate_template stored on a study (JOB-A03, contract 3.4)."""

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from app.services.comfort.lawson_service import lawson_hash
from app.services.simulations import simulation_constants as c

LETTERS = "ABCDEFGHIJ"


def lawson_block(table: Mapping[str, Any]) -> dict[str, Any]:
    """Convert the settings Lawson table to the contract 3.4 shape."""
    comfort = [x for x in table["comfort"] if x["threshold_ms"] is not None]
    return {
        "exceedance": table["exceedance_probability"],
        "comfort": [{"class": LETTERS[i], "key": x["key"], "threshold_ms": x["threshold_ms"]}
                    for i, x in enumerate(comfort)],
        "uncomfortable_class": LETTERS[len(comfort)],
        "safety": [{"key": s["key"], "threshold_ms": s["threshold_ms"],
                    "exceedance": table["safety_probability"]} for s in table["safety"]],
    }


def rose_block(rose: Mapping[str, Any], cache_key: str | None) -> dict[str, Any]:
    """Snapshot the rose fields the solver needs."""
    keys = ("center_deg", "frequency", "weibull_k", "weibull_c_ms")
    return {"cache_key": cache_key, "calm_fraction": rose["calm_fraction"],
            "sectors": [{k: s[k] for k in keys} for s in rose["sectors"]]}


def build_template(
    inputs: Mapping[str, Any], settings: Mapping[str, Any], study_id: UUID,
    output_grid: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Return the template for era5 wind, None for manual wind."""
    if inputs["source"] != "era5" or inputs["rose"] is None:
        return None
    lawson = lawson_block(settings["lawson"])
    turb = settings["turbulence_intensity_default"]
    # Hash the settings form: comfort and report lookups hash the same table.
    digest = lawson_hash(settings["lawson"], turb, inputs["cache_key"])
    pid = str(inputs["id"])
    return {
        "contract_version": 1, "job_kind": "aggregate", "project_id": pid,
        "study_id": str(study_id),
        "output_dir": f"results/{pid}/{study_id}/aggregate-{digest[:12]}",
        "lawson_hash": digest,
        "rose": rose_block(inputs["rose"], inputs["cache_key"]),
        "site": {"z0_m": inputs["z0_m"], "z0_ref_m": c.Z0_REF_M,
                 "blending_height_m": c.BLENDING_HEIGHT_M,
                 "analysis_height_m": inputs["analysis_height_m"]},
        "lawson": lawson, "turbulence_intensity_default": turb,
        "output_grid": dict(output_grid),
    }
