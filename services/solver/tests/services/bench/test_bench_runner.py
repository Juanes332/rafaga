"""SOL-18 benchmark runner."""

import json
import subprocess
import sys

import pytest

from app.services.bench.bench_runner import median_of, shape_for


def test_shape_for_targets_the_node_count() -> None:
    nz, ny, nx = shape_for(25_000_000)
    assert abs(nz * ny * nx - 25_000_000) / 25_000_000 < 0.05


def test_median_of_reports_medians() -> None:
    runs = [{"wall_s": w, "mlups": m, "peak_memory_bytes": 1} for w, m in ((1, 9), (3, 7), (2, 8))]
    assert median_of(runs)["median_wall_s"] == 2 and median_of(runs)["median_mlups"] == 8


@pytest.mark.bench
def test_runner_prints_json_with_medians() -> None:
    out = subprocess.check_output(
        [sys.executable, "-m", "app.services.bench.bench_runner", "--nodes-3d", "200000",
         "--steps-3d", "20", "--runs", "1"], text=True, timeout=1800)
    report = json.loads(out)
    for case in ("plan2d_400x300", "volume3d"):
        assert {"median_wall_s", "median_mlups", "median_peak_memory_bytes"} <= set(report[case])
