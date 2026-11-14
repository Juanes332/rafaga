"""Rows the solver writes on completion: results, comfort, exports, reports."""

import json
from typing import Any

from psycopg import Connection

_RESULT_COLUMNS = ("output_grid", "stats", "convergence", "comparability", "fields", "images",
                   "warnings")


def insert_result(conn: Connection, job: dict[str, Any], manifest: dict[str, Any]) -> None:
    """Insert the results row of a completed heavy job."""
    payload = job["payload"]
    conn.execute(
        "INSERT INTO results (job_id, study_id, project_id, alternative_id, kind, direction_deg,"
        " dx_m, device, output_grid, stats, convergence, comparability, comparability_key, dir,"
        " fields, images, warnings) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (job["id"], job["study_id"], job["project_id"], payload["alternative_id"],
         manifest["kind"], manifest["direction_deg"], manifest["dx_m"], manifest["device"],
         *[json.dumps(manifest[c]) for c in _RESULT_COLUMNS[:4]], manifest["comparability_key"],
         manifest["dir"], *[json.dumps(manifest[c]) for c in _RESULT_COLUMNS[4:]]))


def upsert_comfort(conn: Connection, job: dict[str, Any], row: dict[str, Any]) -> None:
    """Insert (or refresh) the comfort_results row of an aggregate job."""
    conn.execute(
        "INSERT INTO comfort_results (study_id, job_id, lawson_hash, lawson, coverage, partial,"
        " class_areas, safety_areas, dir, fields, images) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        " ON CONFLICT (study_id, lawson_hash) DO UPDATE SET job_id = EXCLUDED.job_id,"
        " lawson = EXCLUDED.lawson, coverage = EXCLUDED.coverage, partial = EXCLUDED.partial,"
        " class_areas = EXCLUDED.class_areas, safety_areas = EXCLUDED.safety_areas,"
        " dir = EXCLUDED.dir, fields = EXCLUDED.fields, images = EXCLUDED.images",
        (job["study_id"] or job["payload"]["study_id"], job["id"], row["lawson_hash"],
         json.dumps(row["lawson"]), row["coverage"], row["partial"], json.dumps(row["class_areas"]),
         json.dumps(row["safety_areas"]), row["dir"], json.dumps(row["fields"]),
         json.dumps(row["images"])))


def set_export_file(conn: Connection, export_id: str, path: str) -> None:
    """Record the produced PNG on its exports row."""
    conn.execute("UPDATE exports SET file = %s WHERE id = %s", (path, export_id))


def set_report_file(conn: Connection, report_id: str, path: str) -> None:
    """Record the produced PDF on its reports row."""
    conn.execute("UPDATE reports SET file = %s WHERE id = %s", (path, report_id))


# Columns the solver may read from api-owned tables (job contract v1.1, section 2.7).
API_OWNED_READS: dict[str, set[str]] = {"alternatives": {"id", "is_base"}}

COMPARABLE_RESULTS_SQL = (
    "SELECT r.id, r.job_id, r.dir, r.direction_deg, r.alternative_id, a.is_base,"
    " j.payload->'scene' AS scene, j.payload->'render' AS render"
    " FROM results r JOIN alternatives a ON a.id = r.alternative_id"
    " JOIN jobs j ON j.id = r.job_id"
    " WHERE r.project_id = %s AND r.comparability_key = %s ORDER BY r.created_at DESC")


def comparable_results(conn: Connection, project_id, comparability_key: str) -> list[dict[str, Any]]:
    """Return the project's results sharing a comparability key, newest first.

    `is_base` comes from the api-owned alternatives table (read only, contract 2.7).
    """
    return conn.execute(COMPARABLE_RESULTS_SQL, (project_id, comparability_key)).fetchall()


def set_result_images(conn: Connection, result_id, images: list[dict]) -> None:
    """Replace the images list of a result row."""
    conn.execute("UPDATE results SET images = %s WHERE id = %s", (json.dumps(images), result_id))
