"""Retention purge of old failed and cancelled jobs (JOB-A02)."""

import asyncio
import logging
import shutil
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.configs.config import Settings

logger = logging.getLogger(__name__)
DAY_SECONDS = 86400


async def purge_old_jobs(session: AsyncSession, settings: Settings) -> int:
    """Delete failed/cancelled jobs older than the retention window.

    Completed jobs are kept, and so are their results. Output
    directories of the deleted jobs are removed from the volume.
    """
    result = await session.execute(
        text(
            "DELETE FROM jobs WHERE status IN ('failed','cancelled') AND "
            "finished_at < now() - make_interval(days => :d) "
            "RETURNING payload->>'output_dir' AS output_dir"
        ),
        {"d": settings.job_retention_days},
    )
    dirs = [r[0] for r in result.all() if r[0]]
    await session.commit()
    for rel in dirs:
        base = Path(settings.data_dir)
        for target in (base / rel, base / f"{rel}.tmp"):
            shutil.rmtree(target, ignore_errors=True)
    return len(dirs)


async def retention_loop(factory: async_sessionmaker[AsyncSession], settings: Settings) -> None:
    """Run the purge once a day until cancelled."""
    while True:
        try:
            async with factory() as session:
                await purge_old_jobs(session, settings)
        except Exception:  # noqa: BLE001 - the loop must survive any failure
            logger.exception("retention_purge_failed")
        await asyncio.sleep(DAY_SECONDS)
