"""Build the study part of a report snapshot (job-contract 3.6)."""

from typing import Any

from app.configs.config import Settings
from app.repositories.comfort import comfort_repository as comfort_repo
from app.repositories.reports.report_repository import study_alternative_name
from app.repositories.results.result_repository import list_study_results
from app.services.comfort.lawson_service import lawson_hash
from app.services.results.result_files import load_field
from app.services.results.zone_calculator import compute_zones, fluid_area


def _zone_areas(settings: Settings, result: dict, th: dict) -> dict[str, Any]:
    """Return the ZoneAreas of one result for the caller's thresholds."""
    k = load_field(settings, result, "K")
    ka, ks, dx = th["k_accel"], th["k_stagnation"], result["dx_m"]
    return {"result_id": str(result["id"]), "wind_from_deg": result["direction_deg"],
            "thresholds": {"k_accel": ka, "k_stagnation": ks},
            "fluid_area_m2": fluid_area(k, dx), "zones": compute_zones(k, dx, ka, ks)}


async def comfort_part(session: Any, study: dict, cfg: dict, include: bool) -> tuple[str | None, Any]:
    """Return the comfort directory and areas under the current hash."""
    template = study["aggregate_template"]
    if not (include and template):
        return None, None
    digest = lawson_hash(cfg["lawson"], cfg["turbulence"], template["rose"].get("cache_key"))
    row = await comfort_repo.find_comfort(session, study["id"], digest)
    if row is None:
        return None, None
    areas = {"coverage": row["coverage"], "partial": row["partial"],
             "class_areas": row["class_areas"], "safety_areas": row["safety_areas"]}
    return row["dir"], areas


async def study_snapshot(session: Any, settings: Settings, study: dict, cfg: dict,
                         include_comfort: bool) -> dict[str, Any] | None:
    """Return one study's snapshot, or None when it has no results."""
    results = [dict(r) for r in await list_study_results(session, study["id"])]
    if not results:
        return None
    by_dir = [_zone_areas(settings, r, cfg["thresholds"]) for r in results]
    comfort_dir, comfort_areas = await comfort_part(session, study, cfg, include_comfort)
    return {
        "study_id": str(study["id"]), "kind": study["kind"], "dx_m": study["dx_m"],
        "alternative_name": await study_alternative_name(session, study["id"]),
        "device": results[0]["device"],
        "results": [{"result_dir": r["dir"], "wind_from_deg": r["direction_deg"],
                     "convergence": r["convergence"]} for r in results],
        "zone_areas": by_dir[0], "zone_areas_by_direction": by_dir,
        "comfort_dir": comfort_dir, "comfort_areas": comfort_areas,
    }
