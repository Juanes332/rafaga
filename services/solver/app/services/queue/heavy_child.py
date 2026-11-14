"""Entry point of the spawned heavy-job process (ADR-22)."""

import time
from multiprocessing.queues import Queue
from multiprocessing.synchronize import Event

from app.configs.config import Settings
from app.core.errors.job_error_mapper import to_job_error
from app.core.errors.solver_errors import JobCancelledError
from app.core.logging.logging_config import configure_logging


def run_heavy_child(job: dict, settings: dict, progress: Queue, cancel: Event, result: Queue) -> None:
    """Run the job and post ('ok', manifest) / ('error', ...) / ('cancelled',)."""
    from app.services.simulation.heavy_job_service import run_heavy_job  # noqa: PLC0415

    cfg = Settings(**settings)
    configure_logging(cfg.log_level)
    last = [0.0]

    def report(fraction: float, phase: str, eta: int | None) -> bool:
        """Forward progress at most twice a second; return the cancel flag."""
        now = time.monotonic()
        if now - last[0] >= 0.5:
            progress.put((fraction, phase, eta))
            last[0] = now
        return cancel.is_set()

    try:
        manifest = run_heavy_job(job["payload"], str(job["id"]), cfg, report,
                                 lambda device: progress.put(("device", device)))
        result.put(("ok", manifest))
    except JobCancelledError:
        result.put(("cancelled",))
    except BaseException as exc:  # noqa: BLE001  (every failure must reach the parent)
        result.put(("error", *to_job_error(exc)))
