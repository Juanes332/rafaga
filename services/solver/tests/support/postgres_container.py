"""Disposable Postgres in Docker for integration tests (kernel-assigned port)."""

import subprocess
import time
from pathlib import Path

import psycopg

DDL = Path(__file__).resolve().parents[1] / "fixtures" / "db" / "job_contract.sql"
TABLES = "jobs, studies, results, comfort_results, exports, reports, solver_nodes"


def start() -> tuple[str, str]:
    """Start postgres:16-alpine on a free host port; return (container, url)."""
    container = subprocess.check_output(
        ["docker", "run", "-d", "--rm", "-p", "127.0.0.1:0:5432", "-e", "POSTGRES_PASSWORD=test",
         "postgres:16-alpine"], text=True).strip()
    mapping = subprocess.check_output(["docker", "port", container, "5432"], text=True)
    port = mapping.strip().splitlines()[0].rsplit(":", 1)[1]
    url = f"postgresql://postgres:test@127.0.0.1:{port}/postgres"
    _wait(url)
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(DDL.read_text(encoding="utf-8"))
    return container, url


def _wait(url: str, timeout: float = 60.0) -> None:
    """Block until the server accepts connections (initdb restarts once)."""
    deadline, ok = time.monotonic() + timeout, 0
    while time.monotonic() < deadline:
        try:
            with psycopg.connect(url, connect_timeout=2) as conn:
                conn.execute("SELECT 1")
            ok += 1
            if ok >= 3:
                return
        except psycopg.Error:
            ok = 0
        time.sleep(0.5)
    raise RuntimeError("postgres did not start")


def stop(container: str) -> None:
    """Stop (and thereby remove) the container."""
    subprocess.run(["docker", "stop", container], capture_output=True, check=False)


def reset(url: str) -> None:
    """Empty every shared table between tests."""
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(f"TRUNCATE {TABLES}, users, projects, alternatives CASCADE")
