"""Device probe CLI (SOL-03, ADR-17)."""

import json
import subprocess
import sys

import pytest

from tests.support.gpu_marks import requires_gpu


@pytest.mark.gpu
@requires_gpu
def test_probe_exits_zero_after_running_a_kernel() -> None:
    proc = subprocess.run([sys.executable, "-m", "app.services.device.device_probe"],
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0
    report = json.loads(proc.stdout)
    assert report["ok"] and report["gpu_name"] and report["vram_total_bytes"] > 0


def test_probe_fails_without_cuda(monkeypatch) -> None:
    from app.services.device import device_probe

    def broken():
        raise RuntimeError("no CUDA device visible")

    monkeypatch.setattr(device_probe, "probe", broken)
    assert device_probe.main() == 1
