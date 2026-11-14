"""SQL of the job lifecycle, verbatim from job-contract.md section 4."""

import json
from typing import Any

from psycopg import Connection

CLAIM_SQL = """
UPDATE jobs SET status = 'running', worker_id = %(worker)s, started_at = now(),
               heartbeat_at = now(), attempts = attempts + 1, phase = 'preparing'
WHERE id = (
  SELECT id FROM jobs
  WHERE status = 'queued' AND lane = %(lane)s AND NOT cancel_requested
  ORDER BY priority DESC, created_at
  FOR UPDATE SKIP LOCKED
  LIMIT 1)
RETURNING *;
"""

PROGRESS_SQL = """
UPDATE jobs SET progress = %s, phase = %s, eta_seconds = %s, heartbeat_at = now()
WHERE id = %s AND status = 'running'
RETURNING cancel_requested;
"""

RECOVER_SQL = """
UPDATE jobs SET status='failed', resumable=true, error_code='worker_restarted', finished_at=now()
WHERE status='running' AND heartbeat_at < now() - make_interval(secs => %s)
RETURNING id, payload->>'output_dir' AS output_dir;
"""


def contract_version(conn: Connection) -> str | None:
    """Return schema_meta.job_contract_version, or None before migrations."""
    row = conn.execute(
        "SELECT value FROM schema_meta WHERE key = 'job_contract_version'"
    ).fetchone()
    return row["value"] if row else None


def claim(conn: Connection, worker_id: str, lane: str) -> dict[str, Any] | None:
    """Claim the next queued job of a lane (one transaction)."""
    with conn.transaction():
        return conn.execute(CLAIM_SQL, {"worker": worker_id, "lane": lane}).fetchone()


def update_progress(conn: Connection, job_id, progress: float, phase: str | None,
                    eta: int | None) -> bool | None:
    """Store progress; return cancel_requested (None if no longer running)."""
    with conn.transaction():
        row = conn.execute(PROGRESS_SQL, (progress, phase, eta, job_id)).fetchone()
    return None if row is None else bool(row["cancel_requested"])


def mark_completed(conn: Connection, job_id, device: str | None = None) -> None:
    """Mark a running job completed (caller owns the transaction)."""
    conn.execute(
        "UPDATE jobs SET status='completed', progress=1, phase=NULL, eta_seconds=0, "
        "finished_at=now(), device_used=COALESCE(%s, device_used) WHERE id = %s",
        (device, job_id))


def mark_failed(conn: Connection, job_id, code: str, message: str, details: dict) -> None:
    """Mark a job failed with a contract error code."""
    conn.execute(
        "UPDATE jobs SET status='failed', error_code=%s, error_message=%s, error_details=%s, "
        "phase=NULL, finished_at=now() WHERE id = %s",
        (code, message[:2000], json.dumps(details), job_id))


def mark_cancelled(conn: Connection, job_id) -> None:
    """Mark a job cancelled."""
    conn.execute(
        "UPDATE jobs SET status='cancelled', phase=NULL, finished_at=now() WHERE id = %s",
        (job_id,))


def recover_orphans(conn: Connection, older_than_s: float) -> list[dict[str, Any]]:
    """Fail running jobs whose heartbeat is stale; return their output dirs."""
    with conn.transaction():
        return conn.execute(RECOVER_SQL, (older_than_s,)).fetchall()


def set_device(conn: Connection, job_id, device: str) -> None:
    """Record the device a job actually runs on."""
    conn.execute("UPDATE jobs SET device_used = %s WHERE id = %s", (device, job_id))
