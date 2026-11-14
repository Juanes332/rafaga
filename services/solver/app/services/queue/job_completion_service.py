"""Terminal transitions in one transaction + the aggregate rule (SOL-20)."""

from collections.abc import Callable
from typing import Any

from psycopg import Connection

from app.repositories.jobs import job_repository as jobs
from app.repositories.jobs import study_repository as studies
from app.repositories.results import result_repository as results

HEAVY_KINDS = ("plan2d", "section2d", "volume3d")


def _maybe_enqueue_aggregate(conn: Connection, study: dict[str, Any]) -> bool:
    """Insert the study's aggregate when this was its last heavy job."""
    template = study["aggregate_template"]
    if template is None or studies.open_heavy_jobs(conn, study["id"]) > 0:
        return False
    refs = studies.result_refs(conn, study["id"])
    if not refs or studies.aggregate_exists(conn, study["id"], template["lawson_hash"]):
        return False
    studies.insert_aggregate(conn, study, dict(template) | {"result_refs": refs})
    return True


def finish(conn: Connection, job: dict[str, Any], transition: Callable[[Connection], None]) -> bool:
    """Run a terminal transition; for heavy jobs apply the 3.4 rule.

    The study row is locked first so two jobs finishing at once
    serialise and exactly one of them sees itself as the last.
    """
    with conn.transaction():
        study = None
        if job["kind"] in HEAVY_KINDS and job.get("study_id"):
            study = studies.lock_study(conn, job["study_id"])
        transition(conn)
        return _maybe_enqueue_aggregate(conn, study) if study else False


def complete_heavy(conn: Connection, job: dict, manifest: dict) -> bool:
    """Insert results and complete the job."""
    def apply(c: Connection) -> None:
        """Insert the result row and complete the job."""
        results.insert_result(c, job, manifest)
        jobs.mark_completed(c, job["id"], manifest.get("device"))
    return finish(conn, job, apply)


def complete_light(conn: Connection, job: dict, outcome: Any) -> None:
    """Record a light job's artefact and complete it."""
    def apply(c: Connection) -> None:
        """Record the artefact on its row and complete the job."""
        kind, payload = job["kind"], job["payload"]
        if kind == "aggregate":
            results.upsert_comfort(c, job, outcome)
        elif kind == "render":
            results.set_export_file(c, payload["export_id"], outcome)
        elif kind == "report":
            results.set_report_file(c, payload["report_id"], outcome)
        jobs.mark_completed(c, job["id"])
    finish(conn, job, apply)


def fail(conn: Connection, job: dict, code: str, message: str, details: dict) -> bool:
    """Mark the job failed (and maybe enqueue the aggregate)."""
    return finish(conn, job, lambda c: jobs.mark_failed(c, job["id"], code, message, details))


def cancel(conn: Connection, job: dict) -> bool:
    """Mark the job cancelled (and maybe enqueue the aggregate)."""
    return finish(conn, job, lambda c: jobs.mark_cancelled(c, job["id"]))
