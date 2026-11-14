"""Benchmarks for NFR-01/02/03 evidence (SOL-18).

`python -m app.services.bench.bench_runner [--device auto|cpu|gpu]
[--nodes-3d N] [--steps-3d S] [--runs R]` runs the versioned 400x300
plan2d job end to end and a D3Q19 lattice for a fixed number of steps,
R times each, and prints medians as JSON.
"""

import argparse
import json
import resource
import statistics
import tempfile
import time
from pathlib import Path

from app.configs.config import Settings
from app.services.bench.bench_memory import PeakMemory
from app.services.device.array_module import cupy_or_none
from app.services.simulation.heavy_job_service import make_stepper, run_heavy_job
from app.services.simulation.synthetic_problem import BENCH_CASE_VERSION, synthetic_problem

CASE_2D = Path(__file__).with_name("cases") / "plan2d_400x300.v1.json"


def bench_2d(device: str) -> dict:
    """Run the 400x300 plan2d job once; return wall time, MLUPS and memory."""
    raw = json.loads(CASE_2D.read_text(encoding="utf-8")) | {"device": device}
    with tempfile.TemporaryDirectory() as tmp, PeakMemory(device) as memory:
        start = time.perf_counter()
        manifest = run_heavy_job(raw, "bench", Settings(data_dir=tmp, rafaga_device=device),
                                 lambda *_: False)
        wall = time.perf_counter() - start
    perf = manifest["performance"]
    return {"wall_s": round(wall, 2), "mlups": perf["mlups"], "steps": perf["steps"],
            "converged": manifest["convergence"]["converged"],
            "peak_memory_bytes": memory.peak}


def shape_for(nodes: int) -> tuple[int, int, int]:
    """Return a (nz, ny, nx) box of about `nodes` with BR-16-like proportions."""
    unit = round((nodes / (1 * 2 * 3.6)) ** (1 / 3))
    return unit, 2 * unit, round(3.6 * unit)


def bench_3d(device: str, nodes: int, steps: int) -> dict:
    """Time `steps` D3Q19 LES steps on a synthetic obstacle box."""
    with PeakMemory(device) as memory:
        stepper = make_stepper(synthetic_problem(shape_for(nodes)), device)
        stepper.step(5, accumulate=True)
        sync = getattr(stepper, "synchronize", lambda: None)
        sync()
        start = time.perf_counter()
        stepper.step(steps, accumulate=True)
        sync()
        wall = time.perf_counter() - start
        stepper.close()
    return {"nodes": stepper.problem.nodes, "steps": steps, "wall_s": round(wall, 2),
            "mlups": round(stepper.problem.nodes * steps / wall / 1e6, 2),
            "peak_memory_bytes": memory.peak}


def median_of(runs: list[dict]) -> dict:
    """Return medians of the numeric keys plus the raw runs."""
    keys = ("wall_s", "mlups", "peak_memory_bytes")
    return {f"median_{k}": statistics.median(r[k] for r in runs) for k in keys} | {"runs": runs}


def main() -> None:
    """Parse arguments, run both cases and print the JSON report."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "gpu"])
    parser.add_argument("--nodes-3d", type=int, default=None)
    parser.add_argument("--steps-3d", type=int, default=None)
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    device = args.device if args.device != "auto" else ("gpu" if cupy_or_none() else "cpu")
    nodes = args.nodes_3d or (25_000_000 if device == "gpu" else 3_000_000)
    steps = args.steps_3d or (1000 if device == "gpu" else 30)
    report = {"case_version": BENCH_CASE_VERSION, "device": device,
              "plan2d_400x300": median_of([bench_2d(device) for _ in range(args.runs)]),
              "volume3d": median_of([bench_3d(device, nodes, steps) for _ in range(args.runs)]),
              "host_peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
