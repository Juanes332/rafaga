"""Write fields, previews, viewer and manifest.json of one result (SOL-11)."""

from pathlib import Path

import numpy as np

from app.services.postprocess.comparability_service import comparability, comparability_key
from app.services.postprocess.field_writer import field_stats, write_fields, write_json
from app.services.postprocess.output_fields import plan_output, section_output
from app.services.postprocess.preview_service import write_previews
from app.services.postprocess.slice_images import write_slice_images
from app.services.postprocess.viewer3d_service import write_viewer
from app.services.simulation.simulation_case import SimulationCase
from app.services.simulation.simulation_runner import RunOutcome


def write_result(case: SimulationCase, avg_u: np.ndarray, avg_u2: np.ndarray,
                 outcome: RunOutcome, out_dir: Path, meta: dict) -> dict:
    """Write every artefact into out_dir and return the manifest."""
    p = case.payload
    section = p.job_kind == "section2d"
    fields = section_output(case, avg_u) if section else plan_output(case, avg_u, avg_u2)
    entries = write_fields(fields, out_dir)
    images = write_previews(fields, p, out_dir, section)
    warnings = list(case.warnings)
    if outcome.monitor.cap_reached:
        warnings.append({"code": "convergence_cap_reached", "ref": p.scene.source_ref()})
    if outcome.mach_spikes:
        warnings.append({"code": "local_mach_spikes", "ref": p.scene.source_ref()})
    if p.job_kind == "volume3d":
        write_json(out_dir / "volume" / "viewer3d.json", write_viewer(case, avg_u, out_dir))
        images += write_slice_images(case, avg_u, fields, out_dir)
    cmp = comparability(p)
    manifest = {
        "contract_version": 1, "solver_version": meta["solver_version"], "job_id": meta["job_id"],
        "kind": p.job_kind, "direction_deg": float(p.wind.wind_from_deg), "dx_m": float(p.grid.sim.dx_m),
        "device": meta["device"], "output_grid": p.grid.output.model_dump(exclude_none=True),
        "stats": field_stats(fields), "convergence": outcome.monitor.report(outcome.averaged_steps),
        "comparability": cmp, "comparability_key": comparability_key(cmp),
        "fields": entries, "images": images, "warnings": warnings,
        "performance": {"steps": outcome.steps, "wall_s": round(outcome.wall_s, 3),
                        "mlups": round(outcome.mlups, 2)},
    }
    # Scene copy for maps drawn later (delta.png, report figures).
    write_json(out_dir / "scene.json", p.scene.model_dump(mode="json"))
    write_json(out_dir / "manifest.json", manifest)
    return manifest
