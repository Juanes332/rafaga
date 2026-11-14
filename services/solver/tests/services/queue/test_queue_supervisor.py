"""Queue supervisor against a real Postgres (SOL-02, SOL-03, SOL-04)."""

import threading
import time
from pathlib import Path

import pytest

from tests.support import db_seed
from tests.support.supervisor_harness import settings, supervisor, wait_status

pytestmark = pytest.mark.integration


def _fake_light(log: list, lock: threading.Lock):
    """Return a light runner that records and completes jobs."""
    from app.core.db.db_connection import connect
    from app.repositories.jobs.job_repository import mark_completed

    def run(job, cfg):
        with lock:
            log.append(str(job["id"]))
        time.sleep(0.02)
        with connect(cfg.database_url, autocommit=True) as conn:
            mark_completed(conn, job["id"])
    return run


def test_two_supervisors_never_claim_the_same_job(db_url, tmp_path) -> None:
    ids = db_seed.parents(db_url)
    jobs = [db_seed.job(db_url, ids, {"n": i}, kind="render") for i in range(40)]
    log, lock = [], threading.Lock()
    cfg = settings(db_url, str(tmp_path), light_lane_concurrency=3)
    sups = [supervisor(cfg, light_runner=_fake_light(log, lock)) for _ in range(2)]
    try:
        for job_id in jobs:
            wait_status(db_url, job_id, {"completed"}, 30)
    finally:
        for s in sups:
            s.stop()
    assert sorted(log) == sorted(jobs)
    assert all(s.claimed for s in sups)  # both supervisors took part


def test_notify_wakes_the_lane_before_the_poll(db_url, tmp_path) -> None:
    ids = db_seed.parents(db_url)
    log, lock = [], threading.Lock()
    sup = supervisor(settings(db_url, str(tmp_path), poll_interval_s=30),
                     light_runner=_fake_light(log, lock))
    try:
        time.sleep(1.5)
        job_id = db_seed.job(db_url, ids, {}, kind="render")
        _, elapsed = wait_status(db_url, job_id, {"completed"}, 10)
    finally:
        sup.stop()
    assert elapsed < 3


def test_heavy_jobs_never_overlap(db_url, tmp_path) -> None:
    ids = db_seed.parents(db_url)
    payload = {"sleep_s": 1.0, "output_dir": "results/x/y/z"}
    first, second = (db_seed.job(db_url, ids, payload) for _ in range(2))
    sup = supervisor(settings(db_url, str(tmp_path)),
                     heavy_target=__import__("tests.support.child_doubles", fromlist=["x"]).polite_child)
    try:
        a, _ = wait_status(db_url, first, {"failed"}, 30)
        b, _ = wait_status(db_url, second, {"failed"}, 30)
    finally:
        sup.stop()
    assert b["started_at"] >= a["finished_at"] or a["started_at"] >= b["finished_at"]


def test_orphans_are_failed_resumable_and_cleaned(db_url, tmp_path) -> None:
    ids = db_seed.parents(db_url)
    stale = db_seed.job(db_url, ids, {"output_dir": "results/p/s/stale"})
    fresh = db_seed.job(db_url, ids, {"output_dir": "results/p/s/fresh"})
    (tmp_path / "results/p/s/stale.tmp").mkdir(parents=True)
    with db_seed.conn(db_url) as c:
        c.execute("UPDATE jobs SET status='running', heartbeat_at=now()-interval '120 seconds' WHERE id=%s", (stale,))
        c.execute("UPDATE jobs SET status='running', heartbeat_at=now() WHERE id=%s", (fresh,))
    sup = supervisor(settings(db_url, str(tmp_path)))
    try:
        row, _ = wait_status(db_url, stale, {"failed"}, 10)
    finally:
        sup.stop()
    assert row["error_code"] == "worker_restarted" and row["resumable"] is True
    assert not (tmp_path / "results/p/s/stale.tmp").exists()
    assert db_seed.job_row(db_url, fresh)["status"] == "running"


def test_heartbeat_upserts_solver_node(db_url, tmp_path) -> None:
    sup = supervisor(settings(db_url, str(tmp_path)))
    try:
        deadline = time.monotonic() + 10
        row = None
        while time.monotonic() < deadline and row is None:
            with db_seed.conn(db_url) as c:
                row = c.execute("SELECT * FROM solver_nodes").fetchone()
            time.sleep(0.2)
    finally:
        sup.stop()
    assert row["worker_id"] == sup.worker_id and row["device"] == "cpu"
    assert row["cpu_cores"] == 4 and row["solver_version"]
