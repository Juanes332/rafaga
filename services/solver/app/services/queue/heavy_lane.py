"""Heavy lane: one job at a time in a spawned child (ADR-22, SOL-05)."""

import logging
import multiprocessing as mp
import queue
import time
from collections.abc import Callable
from pathlib import Path

import psycopg

from app.configs.config import Settings
from app.core.db.db_connection import connect
from app.repositories.jobs import job_repository as jobs
from app.services.queue import job_completion_service as completion
from app.services.queue.baseline_link_service import safe_link_baseline
from app.services.queue.heavy_child import run_heavy_child
from app.services.storage import output_dir_service as storage

logger = logging.getLogger(__name__)
_CTX = mp.get_context("spawn")


class HeavyLane:
    """Execute claimed heavy jobs in child processes and supervise them."""

    def __init__(self, settings: Settings, target: Callable = run_heavy_child) -> None:
        """Bind settings and the child entry point (a seam for tests)."""
        self.settings = settings
        self.target = target
        self.job_id: str | None = None

    def run(self, job: dict) -> str:
        """Run one job to a terminal state and return that state."""
        self.job_id = str(job["id"])
        progress, result, cancel = _CTX.Queue(), _CTX.Queue(), _CTX.Event()
        child = _CTX.Process(target=self.target, daemon=True, args=(
            _serializable(job), self.settings.model_dump(), progress, cancel, result))
        child.start()
        try:
            with connect(self.settings.database_url, autocommit=True) as conn:
                outcome = self._supervise(conn, job, child, progress, result, cancel)
                return self._finish(conn, job, outcome)
        finally:
            _reap(child)
            self.job_id = None

    def _supervise(self, conn, job, child, progress, result, cancel) -> tuple:
        """Relay progress every <=1 s, honour cancellation, collect the outcome."""
        state, cancel_at = (0.0, "preparing", None), None
        while True:
            try:
                return result.get(timeout=1.0)
            except queue.Empty:
                pass
            state = _drain(progress, state, lambda d: jobs.set_device(conn, job["id"], d))
            requested = jobs.update_progress(conn, job["id"], *state)
            if requested and cancel_at is None:
                cancel.set()
                cancel_at = time.monotonic()
            if cancel_at is not None and self._hard_stop(child, cancel_at):
                return ("cancelled",)
            if not child.is_alive() and result.empty():
                return ("error", "internal_error", "solver process crashed",
                        {"reason": "solver_crashed", "exit_code": child.exitcode})

    def _hard_stop(self, child, cancel_at: float) -> bool:
        """Terminate at 8 s and kill at 9 s after a cancel request."""
        waited = time.monotonic() - cancel_at
        if waited >= self.settings.cancel_kill_after_s and child.is_alive():
            child.terminate()
            child.join(1.0)
            if child.is_alive():
                child.kill()
            return True
        return False

    def _finish(self, conn, job: dict, outcome: tuple) -> str:
        """Write the terminal state, cleaning partial output on failure."""
        final = storage.resolve(self.settings.data_dir, job["payload"].get("output_dir", "invalid"))
        if outcome[0] == "ok":
            try:
                completion.complete_heavy(conn, job, outcome[1])
                safe_link_baseline(conn, self.settings.data_dir, job, outcome[1])
                return "completed"
            except psycopg.Error:
                # A result that cannot be recorded must not leave the job running.
                logger.exception("recording the result failed", extra={"job_id": str(job["id"])})
                outcome = ("error", "internal_error", "result could not be recorded",
                           {"reason": "result_not_recorded"})
        storage.discard(final)
        if outcome[0] == "cancelled":
            completion.cancel(conn, job)
            return "cancelled"
        code, message, details = outcome[1:]
        logger.warning("job failed code=%s", code, extra={"job_id": str(job["id"])})
        completion.fail(conn, job, code, message, details)
        return "failed"


def _drain(progress, state: tuple, on_device: Callable[[str], None]) -> tuple:
    """Return the newest progress tuple; forward device announcements."""
    try:
        while True:
            item = progress.get_nowait()
            if item[0] == "device":
                on_device(item[1])
            else:
                state = item
    except queue.Empty:
        return state


def _reap(child) -> None:
    """Make sure the child is gone so its GPU context is released."""
    child.join(2.0)
    if child.is_alive():
        child.kill()
        child.join(1.0)


def _serializable(job: dict) -> dict:
    """Return the job row with only picklable primitives."""
    return {k: (str(v) if k in ("id", "study_id", "project_id", "owner_id") and v else v)
            for k, v in job.items() if k in ("id", "study_id", "project_id", "kind", "payload")}


def remove_output(settings: Settings, output_dir: str | None) -> None:
    """Delete a job's partial output (orphan recovery)."""
    if output_dir:
        storage.discard(Path(storage.resolve(settings.data_dir, output_dir)))
