"""Supervisor: schema wait, orphan recovery, heartbeat, LISTEN and lanes (SOL-02..04)."""

import logging
import socket
import threading
import uuid
from collections.abc import Callable
from datetime import UTC, datetime

import psycopg

from app.configs.config import SOLVER_VERSION, Settings
from app.core.db.db_connection import connect
from app.repositories.jobs import job_repository as jobs
from app.repositories.nodes.node_repository import upsert_node
from app.services.device.capability_service import detect
from app.services.queue.heavy_child import run_heavy_child
from app.services.queue.heavy_lane import HeavyLane, remove_output
from app.services.queue.light_lane import run_light_job

logger = logging.getLogger(__name__)
CHANNEL = "rafaga_jobs"


class QueueSupervisor:
    """Own the worker threads; expose lane state for /health."""

    def __init__(self, settings: Settings, heavy_target: Callable = run_heavy_child,
                 light_runner: Callable = run_light_job,
                 capabilities: Callable[[], dict] | None = None) -> None:
        """Wire collaborators; nothing runs until start()."""
        self.settings = settings
        self.worker_id = f"{socket.gethostname()}:{uuid.uuid4()}"
        self.heavy = HeavyLane(settings, heavy_target)
        self.light_runner = light_runner
        self.capabilities = capabilities or (
            lambda: detect(settings.rafaga_device, settings.startup_benchmark))
        self.caps: dict = {"device": "cpu", "gpu_name": None}
        self.light_busy = 0
        self.claimed: list[str] = []  # every job id this worker claimed (tests)
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._wake = {"heavy": threading.Event(), "light": threading.Event()}
        self.started_at = datetime.now(UTC)

    def start(self) -> None:
        """Start the bootstrap thread (returns immediately)."""
        threading.Thread(target=self._bootstrap, name="supervisor", daemon=True).start()

    def stop(self) -> None:
        """Ask every loop to exit."""
        self._stop.set()
        for event in self._wake.values():
            event.set()

    def lanes(self) -> dict:
        """Return the lane state reported by /health."""
        return {"heavy": {"busy": self.heavy.job_id is not None, "job_id": self.heavy.job_id},
                "light": {"busy": self.light_busy > 0}}

    def _bootstrap(self) -> None:
        """Wait for the schema, recover orphans, then start the loops."""
        if not self._wait_for_schema():
            return
        self._recover_orphans()
        self.caps = self.capabilities()
        threads = [self._heartbeat, self._listen, lambda: self._lane_loop("heavy")]
        threads += [lambda: self._lane_loop("light")] * self.settings.light_lane_concurrency
        for body in threads:
            threading.Thread(target=body, daemon=True).start()

    def _wait_for_schema(self) -> bool:
        """Poll schema_meta every 5 s until job_contract_version = '1'."""
        while not self._stop.is_set():
            try:
                with connect(self.settings.database_url, autocommit=True) as conn:
                    if jobs.contract_version(conn) == "1":
                        return True
            except psycopg.Error as exc:
                logger.info("waiting for database schema: %s", type(exc).__name__)
            self._stop.wait(5.0)
        return False

    def _recover_orphans(self) -> None:
        """Fail stale running jobs as resumable and drop their output (SOL-04)."""
        with connect(self.settings.database_url, autocommit=True) as conn:
            rows = jobs.recover_orphans(conn, self.settings.orphan_timeout_s)
        for row in rows:
            remove_output(self.settings, row["output_dir"])
        if rows:
            logger.warning("recovered %d orphaned jobs", len(rows))

    def _heartbeat(self) -> None:
        """Upsert solver_nodes every heartbeat interval."""
        while not self._stop.is_set():
            node = dict(self.caps, worker_id=self.worker_id, solver_version=SOLVER_VERSION,
                        started_at=self.started_at)
            self._guarded(lambda: _upsert(self.settings, node))
            self._stop.wait(self.settings.heartbeat_interval_s)

    def _listen(self) -> None:
        """Wake lanes on NOTIFY rafaga_jobs; reconnect on failure."""
        while not self._stop.is_set():
            try:
                with connect(self.settings.database_url, autocommit=True) as conn:
                    conn.execute(f"LISTEN {CHANNEL}")
                    while not self._stop.is_set():
                        for note in conn.notifies(timeout=1.0):
                            self._wake.get(note.payload, self._wake["heavy"]).set()
            except psycopg.Error:
                self._stop.wait(self.settings.poll_interval_s)

    def _lane_loop(self, lane: str) -> None:
        """Claim and run jobs of one lane; poll every poll_interval_s."""
        while not self._stop.is_set():
            job = self._guarded(lambda: self._claim(lane))
            if job is None:
                self._wake[lane].wait(self.settings.poll_interval_s)
                self._wake[lane].clear()
                continue
            self._guarded(lambda: self._run(lane, job))

    def _claim(self, lane: str) -> dict | None:
        """Claim one job for this worker."""
        with connect(self.settings.database_url, autocommit=True) as conn:
            job = jobs.claim(conn, self.worker_id, lane)
        if job:
            with self._lock:
                self.claimed.append(str(job["id"]))
        return job

    def _run(self, lane: str, job: dict) -> None:
        """Dispatch a claimed job to its lane."""
        if lane == "heavy":
            self.heavy.run(job)
            return
        with self._lock:
            self.light_busy += 1
        try:
            self.light_runner(job, self.settings)
        finally:
            with self._lock:
                self.light_busy -= 1

    def _guarded(self, action: Callable):
        """Run an action; log and back off instead of killing the thread."""
        try:
            return action()
        except Exception:  # noqa: BLE001  (loops must survive DB outages)
            logger.exception("supervisor loop error")
            self._stop.wait(self.settings.poll_interval_s)
            return None


def _upsert(settings: Settings, node: dict) -> None:
    """Open a connection and upsert the node row."""
    with connect(settings.database_url, autocommit=True) as conn:
        upsert_node(conn, node)
