"""JOB-A02: retention purge of old failed/cancelled jobs."""

import json
from pathlib import Path

from sqlalchemy import text

from app.configs.config import get_settings
from app.services.jobs.retention_service import purge_old_jobs


async def _job(s, user, project, status: str, age_days: int, out: str) -> None:  # noqa: ANN001
    await s.execute(text(
        "INSERT INTO jobs (project_id, owner_id, kind, lane, status, payload, finished_at) "
        "VALUES (:p, :o, 'plan2d', 'heavy', :s, CAST(:pl AS jsonb), now() - make_interval(days => :d))"),
        {"p": project, "o": user, "s": status, "d": age_days, "pl": json.dumps({"output_dir": out})})


async def test_purge_deletes_old_failed_and_cancelled_keeps_rest(
    app, architect, project
) -> None:  # noqa: ANN001
    """Only failed/cancelled jobs beyond 90 days go, with their dirs."""
    data = Path(get_settings().data_dir)
    for name in ("old", "new", "done"):
        (data / name).mkdir(parents=True)
    async with app.state.session_factory() as s:
        for st, age, out in (("failed", 91, "old"), ("cancelled", 91, "old"),
                             ("failed", 10, "new"), ("completed", 400, "done")):
            await _job(s, architect.id, project["id"], st, age, out)
        await s.commit()
        removed = await purge_old_jobs(s, get_settings())
        left = (await s.execute(text("SELECT status FROM jobs ORDER BY status"))).scalars().all()
    assert removed == 2 and left == ["completed", "failed"]
    assert not (data / "old").exists() and (data / "new").exists() and (data / "done").exists()
