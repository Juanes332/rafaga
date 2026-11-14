"""SOL-05 on a real GPU job: cancelled within 10 s and VRAM released."""

import json
import subprocess
import sys
import time

import pytest

from tests.support import db_seed
from tests.support.gpu_marks import requires_gpu
from tests.support.payload_factory import plan_payload
from tests.support.supervisor_harness import settings, supervisor, wait_status

pytestmark = [pytest.mark.integration, pytest.mark.gpu, requires_gpu]


def _free_vram() -> int:
    code = "import cupy;print(cupy.cuda.runtime.memGetInfo()[0])"
    return int(subprocess.check_output([sys.executable, "-c", code], text=True))


def test_real_gpu_job_cancels_and_frees_memory(db_url, tmp_path) -> None:
    ids = db_seed.parents(db_url)
    raw = plan_payload(dx=0.5, device="gpu", convergence={
        "spinup_ft": 50, "min_avg_ft": 50, "max_avg_ft": 100})
    raw["output_dir"] = "results/p/s/gpu"
    before = _free_vram()
    first = db_seed.job(db_url, ids, raw)
    nxt = db_seed.job(db_url, ids, {"contract_version": 1, "output_dir": "results/p/s/n"})
    sup = supervisor(settings(db_url, str(tmp_path), rafaga_device="auto"))
    try:
        wait_status(db_url, first, {"running"}, 30)
        deadline = time.monotonic() + 60
        while db_seed.job_row(db_url, first)["phase"] != "spinup" and time.monotonic() < deadline:
            time.sleep(0.2)
        assert db_seed.job_row(db_url, first)["device_used"] == "gpu"
        with db_seed.conn(db_url) as c:
            c.execute("UPDATE jobs SET cancel_requested=true WHERE id=%s", (first,))
        asked = time.monotonic()
        wait_status(db_url, first, {"cancelled"}, 12)
        took = time.monotonic() - asked
        wait_status(db_url, nxt, {"failed"}, 30)
    finally:
        sup.stop()
    assert took <= 10.0
    assert _free_vram() >= before - 256 * 1024**2
    assert not (tmp_path / "results/p/s/gpu.tmp").exists()
