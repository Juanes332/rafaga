"""Build the aggregate job payload of job-contract 3.4."""

from typing import Any
from uuid import UUID

from app.services.comfort.lawson_service import lawson_hash, lawson_job_payload


def build_aggregate_payload(
    *, project_id: UUID, study_id: UUID, template: dict[str, Any],
    results: list[dict[str, Any]], lawson: dict[str, Any], turbulence: float,
) -> dict[str, Any]:
    """Return the payload for the caller's current Lawson table."""
    digest = lawson_hash(lawson, turbulence, template["rose"].get("cache_key"))
    return {
        "contract_version": 1, "job_kind": "aggregate", "project_id": str(project_id),
        "study_id": str(study_id),
        "output_dir": f"results/{project_id}/{study_id}/aggregate-{digest[:12]}",
        "lawson_hash": digest,
        "result_refs": [{"result_id": str(r["id"]), "wind_from_deg": r["direction_deg"],
                         "dir": r["dir"]} for r in results],
        "rose": template["rose"], "site": template["site"],
        "lawson": lawson_job_payload(lawson),
        "turbulence_intensity_default": turbulence,
        "output_grid": template["output_grid"],
    }
