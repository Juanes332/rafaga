"""Study-level queries behind the aggregate enqueue rule (contract 3.4)."""

import json
from typing import Any

from psycopg import Connection

TERMINAL = ("completed", "failed", "cancelled")


def lock_study(conn: Connection, study_id) -> dict[str, Any] | None:
    """Lock and return the study row (SELECT ... FOR UPDATE)."""
    return conn.execute(
        "SELECT id, project_id, owner_id, aggregate_template FROM studies WHERE id = %s FOR UPDATE",
        (study_id,)).fetchone()


def open_heavy_jobs(conn: Connection, study_id) -> int:
    """Return how many heavy jobs of the study are not terminal yet."""
    row = conn.execute(
        "SELECT count(*) AS n FROM jobs WHERE study_id = %s AND lane = 'heavy' "
        "AND status NOT IN ('completed', 'failed', 'cancelled')", (study_id,)).fetchone()
    return int(row["n"])


def result_refs(conn: Connection, study_id) -> list[dict[str, Any]]:
    """Return result_refs of the study (contract 3.4)."""
    rows = conn.execute(
        "SELECT id, direction_deg, dir FROM results WHERE study_id = %s ORDER BY created_at",
        (study_id,)).fetchall()
    return [{"result_id": str(r["id"]), "wind_from_deg": r["direction_deg"], "dir": r["dir"]}
            for r in rows]


def aggregate_exists(conn: Connection, study_id, lawson_hash: str) -> bool:
    """Return True if an aggregate with this hash is queued, running or done."""
    row = conn.execute(
        "SELECT 1 FROM jobs WHERE study_id = %s AND kind = 'aggregate' "
        "AND payload->>'lawson_hash' = %s AND status IN ('queued', 'running', 'completed') LIMIT 1",
        (study_id, lawson_hash)).fetchone()
    return row is not None


def insert_aggregate(conn: Connection, study: dict[str, Any], payload: dict[str, Any]) -> None:
    """Insert one light-lane aggregate job (NOTIFY fires by trigger)."""
    conn.execute(
        "INSERT INTO jobs (study_id, project_id, owner_id, kind, lane, priority, payload) "
        "VALUES (%s, %s, %s, 'aggregate', 'light', 10, %s)",
        (study["id"], study["project_id"], study["owner_id"], json.dumps(payload)))
