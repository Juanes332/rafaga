"""Light lane: aggregate, render and report jobs on CPU threads (ADR-22)."""

import logging
import threading
from collections.abc import Callable

import psycopg

from app.configs.config import Settings
from app.core.db.db_connection import connect
from app.core.errors.job_error_mapper import to_job_error
from app.repositories.jobs import job_repository as jobs
from app.services.comfort.aggregate_service import run_aggregate
from app.services.queue import job_completion_service as completion
from app.services.render.render_service import run_render
from app.services.report.report_service import run_report

logger = logging.getLogger(__name__)
RUNNERS: dict[str, Callable] = {"aggregate": run_aggregate, "render": run_render, "report": run_report}


def _heartbeat(job_id, settings: Settings, done: threading.Event) -> None:
    """Refresh progress/heartbeat every second while the job runs."""
    with connect(settings.database_url, autocommit=True) as conn:
        while not done.wait(1.0):
            jobs.update_progress(conn, job_id, 0.5, "rendering", None)


def run_light_job(job: dict, settings: Settings) -> str:
    """Execute one claimed light job and write its terminal state."""
    done = threading.Event()
    beat = threading.Thread(target=_heartbeat, args=(job["id"], settings, done), daemon=True)
    beat.start()
    try:
        return _execute(job, settings)
    finally:
        done.set()
        beat.join(2.0)


def _execute(job: dict, settings: Settings) -> str:
    """Run the job body and record completion or failure."""
    with connect(settings.database_url, autocommit=True) as conn:
        jobs.set_device(conn, job["id"], "cpu")
        try:
            outcome = RUNNERS[job["kind"]](job["payload"], settings)
        except Exception as exc:  # noqa: BLE001  (any failure becomes a job error)
            code, message, details = to_job_error(exc)
            logger.warning("light job failed code=%s", code, extra={"job_id": str(job["id"])})
            completion.fail(conn, job, code, message, details)
            return "failed"
        try:
            completion.complete_light(conn, job, outcome)
        except psycopg.Error:
            logger.exception("recording the artefact failed", extra={"job_id": str(job["id"])})
            completion.fail(conn, job, "internal_error", "artefact could not be recorded",
                            {"reason": "result_not_recorded"})
            return "failed"
        return "completed"
