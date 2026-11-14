"""Study completion -> exactly one aggregate (SOL-20)."""

import copy
import threading

import pytest

from app.core.db.db_connection import connect
from app.services.queue import job_completion_service as completion
from tests.support import db_seed
from tests.support.contracts import example

pytestmark = pytest.mark.integration


def _template() -> dict:
    tpl = copy.deepcopy(example("job.aggregate.example"))
    tpl.pop("result_refs")
    return tpl


def _manifest(job_id: str, wind: float) -> dict:
    m = copy.deepcopy(example("result-manifest.example"))
    return m | {"job_id": job_id, "direction_deg": wind, "dir": f"results/p/s/{job_id}"}


def _running_jobs(url: str, ids: dict, study: str, n: int) -> list[dict]:
    rows = []
    for i in range(n):
        payload = {"alternative_id": ids["alternative"], "output_dir": f"results/p/s/{i}",
                   "wind": {"wind_from_deg": 90.0 * i}}
        job_id = db_seed.job(url, ids, payload, study_id=study)
        with db_seed.conn(url) as c:
            c.execute("UPDATE jobs SET status='running' WHERE id=%s", (job_id,))
        rows.append(db_seed.job_row(url, job_id))
    return rows


def _aggregates(url: str, study: str) -> list[dict]:
    with db_seed.conn(url) as c:
        return c.execute("SELECT * FROM jobs WHERE study_id=%s AND kind='aggregate'", (study,)).fetchall()


def test_two_jobs_finishing_together_enqueue_one_aggregate(db_url) -> None:
    ids = db_seed.parents(db_url)
    study = db_seed.study(db_url, ids, _template())
    rows = _running_jobs(db_url, ids, study, 2)
    barrier = threading.Barrier(2)

    def finish(row):
        with connect(db_url, autocommit=True) as conn:
            barrier.wait()
            completion.complete_heavy(conn, row, _manifest(str(row["id"]), row["direction_deg"] or 0.0))

    threads = [threading.Thread(target=finish, args=(r,)) for r in rows]
    [t.start() for t in threads]
    [t.join() for t in threads]
    aggs = _aggregates(db_url, study)
    assert len(aggs) == 1
    payload = aggs[0]["payload"]
    assert aggs[0]["lane"] == "light" and aggs[0]["priority"] == 10
    assert len(payload["result_refs"]) == 2 and payload["lawson_hash"] == _template()["lawson_hash"]


def test_no_aggregate_without_template_or_results(db_url) -> None:
    ids = db_seed.parents(db_url)
    manual = db_seed.study(db_url, ids, None)
    [row] = _running_jobs(db_url, ids, manual, 1)
    with connect(db_url, autocommit=True) as conn:
        completion.complete_heavy(conn, row, _manifest(str(row["id"]), 0.0))
    era5 = db_seed.study(db_url, ids, _template())
    [row] = _running_jobs(db_url, ids, era5, 1)
    with connect(db_url, autocommit=True) as conn:
        completion.fail(conn, row, "numerical_instability", "x", {})
    assert _aggregates(db_url, manual) == [] and _aggregates(db_url, era5) == []


def test_existing_aggregate_with_same_hash_is_not_duplicated(db_url) -> None:
    ids = db_seed.parents(db_url)
    study = db_seed.study(db_url, ids, _template())
    first, second = _running_jobs(db_url, ids, study, 2)
    with connect(db_url, autocommit=True) as conn:
        completion.complete_heavy(conn, first, _manifest(str(first["id"]), 0.0))
        db_seed.job(db_url, ids, {"lawson_hash": _template()["lawson_hash"]}, kind="aggregate",
                    study_id=study)
        completion.cancel(conn, second)
    assert len(_aggregates(db_url, study)) == 1
