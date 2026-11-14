"""Attach delta.png to alternative results once a comparable baseline exists (US-13).

Runs after a heavy result is recorded. If the new result belongs to the
base alternative, every comparable alternative result of the project
gets (or refreshes) its delta; otherwise the new result is compared with
the newest comparable base result. Comparable = same comparability_key
(direction, z0, U_ref, dx, output grid, z_a), BR-11.
"""

import logging
from typing import Any

from psycopg import Connection

from app.repositories.results import result_repository as results
from app.services.postprocess.delta_service import render_delta

logger = logging.getLogger(__name__)


def _thresholds(row: dict[str, Any]) -> dict:
    """Return the render thresholds frozen in the job payload."""
    return {"dk_reduction": -0.1} | dict(row.get("render") or {})


def link_baseline(conn: Connection, data_dir: str, job: dict, manifest: dict) -> int:
    """Render missing delta images for this result's comparable group; return how many."""
    rows = results.comparable_results(conn, job["project_id"], manifest["comparability_key"])
    base = next((r for r in rows if r["is_base"]), None)
    if base is None:
        return 0
    own = next((r for r in rows if str(r["job_id"]) == str(job["id"])), None)
    if own is None:
        return 0
    targets = [r for r in rows if not r["is_base"]] if own["is_base"] else [own]
    for row in targets:
        images = render_delta(data_dir, row["dir"], base["dir"], row["scene"],
                              row["direction_deg"], _thresholds(row),
                              int((row.get("render") or {}).get("dpi", 150)))
        results.set_result_images(conn, row["id"], images)
    return len(targets)


def safe_link_baseline(conn: Connection, data_dir: str, job: dict, manifest: dict) -> None:
    """Run link_baseline; a failed preview never fails the finished job."""
    try:
        link_baseline(conn, data_dir, job, manifest)
    except Exception:  # noqa: BLE001  (preview only; logged with its trace)
        logger.exception("delta preview failed", extra={"job_id": str(job["id"])})
