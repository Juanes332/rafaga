"""delta.png is attached to every alternative result once its baseline exists."""

import uuid

import pytest

from app.configs.config import Settings
from app.repositories.results import result_repository as results
from app.services.queue.baseline_link_service import link_baseline
from app.services.simulation.heavy_job_service import run_heavy_job
from tests.support import db_seed
from tests.support.payload_factory import plan_payload

pytestmark = pytest.mark.integration


def _result(url: str, ids: dict, alternative: str, data: str, tag: str) -> tuple[dict, dict]:
    raw = plan_payload(dx=8.0, device="cpu")
    raw.update({"alternative_id": alternative, "output_dir": f"results/{ids['project']}/s/{tag}"})
    study = db_seed.study(url, ids)
    job_id = db_seed.job(url, ids, raw, study_id=study)
    manifest = run_heavy_job(raw, job_id, Settings(data_dir=data), lambda *_: False)
    job = db_seed.job_row(url, job_id)
    with db_seed.conn(url) as c:
        results.insert_result(c, job, manifest)
    return job, manifest


def _images(url: str, job_id) -> set[str]:
    with db_seed.conn(url) as c:
        row = c.execute("SELECT images FROM results WHERE job_id = %s", (job_id,)).fetchone()
    return {i["name"] for i in row["images"]}


@pytest.mark.parametrize("base_first", [True, False])
def test_alternative_gets_delta_whatever_finishes_first(db_url, tmp_path, base_first) -> None:
    ids = db_seed.parents(db_url)
    other_alt = str(uuid.uuid4())
    with db_seed.conn(db_url) as c:
        c.execute("UPDATE alternatives SET is_base = true WHERE id = %s", (ids["alternative"],))
        c.execute("INSERT INTO alternatives (id) VALUES (%s)", (other_alt,))
    data = str(tmp_path)
    order = [(ids["alternative"], "base"), (other_alt, "alt")]
    if not base_first:
        order.reverse()
    done = {}
    for alternative, tag in order:
        job, manifest = _result(db_url, ids, alternative, data, tag)
        with db_seed.conn(db_url) as c:
            link_baseline(c, data, job, manifest)
        done[tag] = job
    assert "delta" in _images(db_url, done["alt"]["id"])
    assert "delta" not in _images(db_url, done["base"]["id"])
    assert (tmp_path / f"results/{ids['project']}/s/alt/images/delta.png").exists()
