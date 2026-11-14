"""Insert parents, studies and jobs the way the api would."""

import json
import uuid

import psycopg
from psycopg.rows import dict_row


def conn(url: str) -> psycopg.Connection:
    """Return an autocommit dict-row connection."""
    return psycopg.connect(url, autocommit=True, row_factory=dict_row)


def parents(url: str) -> dict:
    """Insert a user, project and alternative; return their ids."""
    ids = {k: str(uuid.uuid4()) for k in ("user", "project", "alternative")}
    with conn(url) as c:
        c.execute("INSERT INTO users (id) VALUES (%s)", (ids["user"],))
        c.execute("INSERT INTO projects (id) VALUES (%s)", (ids["project"],))
        c.execute("INSERT INTO alternatives (id) VALUES (%s)", (ids["alternative"],))
    return ids


def study(url: str, ids: dict, template: dict | None = None, kind: str = "plan2d") -> str:
    """Insert a study row and return its id."""
    with conn(url) as c:
        row = c.execute(
            "INSERT INTO studies (project_id, alternative_id, owner_id, kind, request, dx_m,"
            " aggregate_template) VALUES (%s,%s,%s,%s,'{}',1.0,%s) RETURNING id",
            (ids["project"], ids["alternative"], ids["user"], kind,
             json.dumps(template) if template else None)).fetchone()
    return str(row["id"])


def job(url: str, ids: dict, payload: dict, kind: str = "plan2d", study_id: str | None = None,
        lane: str | None = None) -> str:
    """Insert a queued job and return its id."""
    lane = lane or ("heavy" if kind in ("plan2d", "section2d", "volume3d") else "light")
    with conn(url) as c:
        row = c.execute(
            "INSERT INTO jobs (study_id, project_id, owner_id, kind, lane, priority, payload,"
            " direction_deg) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (study_id, ids["project"], ids["user"], kind, lane, 0 if lane == "heavy" else 10,
             json.dumps(payload), payload.get("wind", {}).get("wind_from_deg"))).fetchone()
    return str(row["id"])


def job_row(url: str, job_id: str) -> dict:
    """Return the jobs row."""
    with conn(url) as c:
        return c.execute("SELECT * FROM jobs WHERE id = %s", (job_id,)).fetchone()
