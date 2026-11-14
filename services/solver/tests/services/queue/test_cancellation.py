"""Cancellation and crash handling of the heavy lane (SOL-05)."""

import time

import pytest

from tests.support import child_doubles, db_seed
from tests.support.supervisor_harness import settings, supervisor, wait_status

pytestmark = pytest.mark.integration


def _cancel_after_running(url: str, job_id: str) -> float:
    wait_status(url, job_id, {"running"}, 20)
    time.sleep(1.0)
    with db_seed.conn(url) as c:
        c.execute("UPDATE jobs SET cancel_requested=true WHERE id=%s AND status='running'", (job_id,))
    return time.monotonic()


@pytest.mark.parametrize("target", [child_doubles.polite_child, child_doubles.sleepy_child])
def test_cancel_reaches_cancelled_within_10s_and_next_job_starts(db_url, tmp_path, target) -> None:
    ids = db_seed.parents(db_url)
    payload = {"output_dir": "results/p/s/a"}
    first = db_seed.job(db_url, ids, payload)
    second = db_seed.job(db_url, ids, {"output_dir": "results/p/s/b", "sleep_s": 0.5})
    sup = supervisor(settings(db_url, str(tmp_path)), heavy_target=target)
    try:
        asked = _cancel_after_running(db_url, first)
        row, _ = wait_status(db_url, first, {"cancelled"}, 12)
        took = time.monotonic() - asked
        wait_status(db_url, second, {"running", "failed", "cancelled"}, 15)
    finally:
        sup.stop()
    assert took <= 10.0
    assert row["finished_at"] is not None


def test_crashing_child_fails_the_job_but_not_the_supervisor(db_url, tmp_path) -> None:
    ids = db_seed.parents(db_url)
    crash = db_seed.job(db_url, ids, {"output_dir": "results/p/s/c"})
    after = db_seed.job(db_url, ids, {"output_dir": "results/p/s/d", "sleep_s": 0.2})
    sup = supervisor(settings(db_url, str(tmp_path)), heavy_target=child_doubles.crashing_child)
    try:
        row, _ = wait_status(db_url, crash, {"failed"}, 20)
        wait_status(db_url, after, {"failed"}, 20)
    finally:
        sup.stop()
    assert row["error_code"] == "internal_error"
    assert row["error_details"]["reason"] == "solver_crashed"


def test_unrecordable_result_fails_instead_of_hanging(db_url, tmp_path) -> None:
    ids = db_seed.parents(db_url)
    orphan = db_seed.job(db_url, ids, {"output_dir": "results/p/s/o", "alternative_id": ids["alternative"]})
    sup = supervisor(settings(db_url, str(tmp_path)), heavy_target=child_doubles.ok_child)
    try:
        row, _ = wait_status(db_url, orphan, {"failed", "completed"}, 20)
    finally:
        sup.stop()
    assert row["status"] == "failed" and row["error_details"]["reason"] == "result_not_recorded"
