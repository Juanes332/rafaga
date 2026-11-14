"""Produce real (coarse) results on disk for light-lane tests."""

import copy
from dataclasses import dataclass
from pathlib import Path

from app.configs.config import Settings
from app.services.simulation.heavy_job_service import run_heavy_job
from tests.support.contracts import example
from tests.support.payload_factory import plan_payload

PROJECT, STUDY = "00000000-0000-4000-8000-000000000001", "00000000-0000-4000-8000-000000000003"


@dataclass
class ResultStore:
    """Data dir with two plan2d results of the same project grid."""

    settings: Settings
    dirs: dict[float, str]
    output_grid: dict


def build_store(root: Path) -> ResultStore:
    """Run two coarse CPU plan2d jobs (wind from 270 and 180 degrees)."""
    settings = Settings(data_dir=str(root), rafaga_device="cpu")
    dirs, grid = {}, None
    for i, wind in enumerate((270.0, 180.0)):
        raw = plan_payload(dx=6.0, wind_from=wind, device="cpu")
        raw["output_dir"] = f"results/{PROJECT}/{STUDY}/job-{i}"
        manifest = run_heavy_job(raw, f"job-{i}", settings, lambda *_: False)
        dirs[wind] = manifest["dir"]
        grid = manifest["output_grid"]
    return ResultStore(settings, dirs, grid)


def aggregate_payload(store: ResultStore) -> dict:
    """Return the contract aggregate example pointed at the stored results."""
    raw = copy.deepcopy(example("job.aggregate.example"))
    raw["result_refs"] = [{"result_id": f"r{i}", "wind_from_deg": w, "dir": d}
                          for i, (w, d) in enumerate(store.dirs.items())]
    raw["output_grid"] = store.output_grid
    return raw
