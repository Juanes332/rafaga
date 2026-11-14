"""Compose the /health answer from the supervisor and a DB ping."""

from collections.abc import Callable

from app.models.health.health_schemas import HealthResponse

_IDLE = {"heavy": {"busy": False, "job_id": None}, "light": {"busy": False}}


class HealthService:
    """Report device, DB and lane state without ever blocking on compute."""

    def __init__(self, ping: Callable[[], bool], supervisor=None) -> None:
        """Bind the DB ping and the (optional) supervisor."""
        self.ping = ping
        self.supervisor = supervisor

    def check(self) -> HealthResponse:
        """Return the current health snapshot."""
        db_ok = self.ping()
        caps = self.supervisor.caps if self.supervisor else {"device": "cpu", "gpu_name": None}
        lanes = self.supervisor.lanes() if self.supervisor else _IDLE
        return HealthResponse(
            status="ok" if db_ok else "degraded", device=caps["device"],
            gpu_name=caps.get("gpu_name"), db="ok" if db_ok else "down", lanes=lanes,
        )
