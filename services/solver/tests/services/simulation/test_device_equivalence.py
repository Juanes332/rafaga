"""SOL-17: same seeded payload on NumPy and CuPy, mean K within 2 %."""

import json
from pathlib import Path

import pytest

from app.configs.config import Settings
from app.services.simulation.heavy_job_service import run_heavy_job
from tests.support.gpu_marks import requires_gpu
from tests.support.payload_factory import plan_payload

pytestmark = [pytest.mark.gpu, requires_gpu]


@pytest.mark.parametrize("kind,dx", [("plan2d", 4.0), ("volume3d", 8.0)])
def test_mean_k_gpu_vs_cpu_within_two_percent(tmp_path: Path, kind, dx) -> None:
    means = {}
    for device in ("cpu", "gpu"):
        raw = plan_payload(dx=dx, kind=kind, device=device)
        raw["output_dir"] = f"results/p/s/{device}"
        manifest = run_heavy_job(raw, device, Settings(data_dir=str(tmp_path)), lambda *_: False)
        assert manifest["device"] == device
        means[device] = manifest["stats"]["k_mean"]
    assert abs(means["gpu"] - means["cpu"]) / means["cpu"] <= 0.02
