"""System domain business logic: liveness and solver status."""

from fastapi import Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.config import Settings, get_settings
from app.core.database.database import get_session
from app.models.system.system_schemas import (
    HealthResponse,
    SolverStatus,
    SystemStatusResponse,
)
from app.repositories.system import system_repository as repo


class SystemService:
    """Report whether the api, the database and the solver are alive."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        """Bind collaborators."""
        self._session = session
        self._settings = settings

    async def db_is_up(self) -> bool:
        """Return whether Postgres answers."""
        try:
            await repo.ping(self._session)
        except (SQLAlchemyError, OSError):
            return False
        return True

    async def health(self) -> HealthResponse:
        """Return the liveness body (degraded when the db is down)."""
        up = await self.db_is_up()
        return HealthResponse(
            status="ok" if up else "degraded",
            db="ok" if up else "down",
            version=self._settings.app_version,
        )

    async def status(self) -> SystemStatusResponse:
        """Return api, db and solver capabilities."""
        if not await self.db_is_up():
            return SystemStatusResponse(db="down", solver=SolverStatus(online=False))
        row = await repo.freshest_solver_node(self._session)
        if row is None:
            return SystemStatusResponse(db="ok", solver=SolverStatus(online=False))
        solver = SolverStatus(**{k: row[k] for k in SolverStatus.model_fields if k != "online"},
                              online=bool(row["online"]))
        return SystemStatusResponse(db="ok", solver=solver)


def get_system_service(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> SystemService:
    """Provide the system service for a request."""
    return SystemService(session, settings)
