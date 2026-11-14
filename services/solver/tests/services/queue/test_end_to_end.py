"""Real jobs through the supervisor: plan2d -> results -> aggregate -> render/report."""

import copy
from pathlib import Path

import pytest

from tests.support import db_seed
from tests.support.contracts import example
from tests.support.payload_factory import plan_payload
from tests.support.supervisor_harness import settings, supervisor, wait_status

pytestmark = pytest.mark.integration


def test_plan2d_completes_inserts_result_and_triggers_lawson(db_url, tmp_path) -> None:
    ids = db_seed.parents(db_url)
    tpl = copy.deepcopy(example("job.aggregate.example"))
    tpl.pop("result_refs")
    tpl["output_dir"] = f"results/{ids['project']}/agg"
    raw = plan_payload(dx=6.0, device="cpu")
    tpl["output_grid"] = raw["grid"]["output"]
    study = db_seed.study(db_url, ids, tpl)
    raw.update({"alternative_id": ids["alternative"], "study_id": study,
                "output_dir": f"results/{ids['project']}/{study}/j1"})
    job_id = db_seed.job(db_url, ids, raw, study_id=study)
    sup = supervisor(settings(db_url, str(tmp_path)))
    try:
        row, _ = wait_status(db_url, job_id, {"completed", "failed"}, 300)
        assert row["status"] == "completed", row["error_message"]
        with db_seed.conn(db_url) as c:
            result = c.execute("SELECT * FROM results WHERE job_id=%s", (job_id,)).fetchone()
            agg = c.execute("SELECT id FROM jobs WHERE kind='aggregate'").fetchone()
        agg_row, _ = wait_status(db_url, str(agg["id"]), {"completed", "failed"}, 60)
    finally:
        sup.stop()
    assert row["progress"] == 1 and row["device_used"] == "cpu"
    assert result["dir"] == raw["output_dir"] and result["stats"]["k_mean"] > 0
    assert (tmp_path / result["dir"] / "images/k.png").exists()
    assert agg_row["status"] == "completed", agg_row["error_message"]
    with db_seed.conn(db_url) as c:
        comfort = c.execute("SELECT * FROM comfort_results").fetchone()
    assert comfort["lawson_hash"] == tpl["lawson_hash"] and comfort["partial"] is True


def test_invalid_payload_fails_with_contract_code(db_url, tmp_path) -> None:
    ids = db_seed.parents(db_url)
    bad = db_seed.job(db_url, ids, {"contract_version": 1, "job_kind": "plan2d", "output_dir": "results/x"})
    old = db_seed.job(db_url, ids, {"contract_version": 9, "output_dir": "results/y"})
    sup = supervisor(settings(db_url, str(tmp_path)))
    try:
        a, _ = wait_status(db_url, bad, {"failed"}, 60)
        b, _ = wait_status(db_url, old, {"failed"}, 60)
    finally:
        sup.stop()
    assert a["error_code"] == "invalid_payload" and a["error_details"]["path"]
    assert b["error_code"] == "contract_version_mismatch"


def test_render_job_sets_export_file_and_missing_result_fails(db_url, tmp_path) -> None:
    from tests.support.result_store import build_store

    store = build_store(tmp_path)
    ids = db_seed.parents(db_url)
    raw = copy.deepcopy(example("job.render.example"))
    raw.update({"layer": "k", "result_dir": store.dirs[270.0], "compare_result_dir": None,
                "output_grid": store.output_grid, "output_dir": f"exports/{ids['user']}"})
    job_id = db_seed.job(db_url, ids, raw, kind="render")
    missing = db_seed.job(db_url, ids, raw | {"result_dir": "results/none"}, kind="render")
    with db_seed.conn(db_url) as c:
        c.execute("INSERT INTO exports (id, owner_id, project_id, job_id, layer, params) "
                  "VALUES (%s, %s, %s, %s, 'k', '{}')",
                  (raw["export_id"], ids["user"], ids["project"], job_id))
    sup = supervisor(settings(db_url, str(tmp_path)))
    try:
        done, _ = wait_status(db_url, job_id, {"completed", "failed"}, 60)
        failed, _ = wait_status(db_url, missing, {"completed", "failed"}, 60)
    finally:
        sup.stop()
    assert done["status"] == "completed"
    with db_seed.conn(db_url) as c:
        file = c.execute("SELECT file FROM exports").fetchone()["file"]
    assert (tmp_path / file).exists() and file.endswith(".png")
    assert failed["status"] == "failed" and failed["error_code"] == "io_error"
