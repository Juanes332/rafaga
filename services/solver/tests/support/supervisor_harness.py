"""Start supervisors against the test database and wait for job states."""

import time

from app.configs.config import Settings
from app.services.queue.queue_supervisor import QueueSupervisor
from tests.support.db_seed import job_row

FAKE_CAPS = {"device": "cpu", "gpu_name": None, "vram_total_bytes": None, "vram_free_bytes": None,
             "ram_total_bytes": 8 * 1024**3, "ram_budget_bytes": 4 * 1024**3, "cpu_cores": 4,
             "mlups_2d": 20.0, "mlups_3d": 5.0}


def settings(url: str, data_dir: str, **extra) -> Settings:
    """Return worker settings bound to the test DB."""
    base = {"database_url": url, "data_dir": data_dir, "poll_interval_s": 0.5,
            "heartbeat_interval_s": 0.5, "startup_benchmark": False, "rafaga_device": "cpu"}
    return Settings(**(base | extra))


def supervisor(cfg: Settings, **kwargs) -> QueueSupervisor:
    """Start a supervisor with fake capabilities."""
    sup = QueueSupervisor(cfg, capabilities=lambda: dict(FAKE_CAPS), **kwargs)
    sup.start()
    return sup


def wait_status(url: str, job_id: str, statuses: set[str], timeout: float) -> tuple[dict, float]:
    """Poll until the job reaches one of statuses; return row and elapsed."""
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        row = job_row(url, job_id)
        if row["status"] in statuses:
            return row, time.monotonic() - start
        time.sleep(0.1)
    raise AssertionError(f"job {job_id} stuck in {job_row(url, job_id)['status']}")
