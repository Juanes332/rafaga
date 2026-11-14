"""Solver entry point: FastAPI factory serving /health plus the queue worker."""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.configs.config import get_settings
from app.core.db.db_connection import ping
from app.core.errors.error_handlers import register_error_handlers
from app.core.logging.logging_config import configure_logging
from app.routers.health import health_router
from app.services.health.health_service import HealthService
from app.services.queue.queue_supervisor import QueueSupervisor


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start the supervisor with the app and stop it on shutdown."""
    supervisor = app.state.supervisor
    if supervisor is not None:
        supervisor.start()
    yield
    if supervisor is not None:
        supervisor.stop()


def create_app() -> FastAPI:
    """Build the app; the worker starts only when WORKER_ENABLED and a DB is set."""
    settings = get_settings()
    configure_logging(settings.log_level)
    # Slab threads already use every core; nested BLAS threads would
    # oversubscribe the CPU in spawned children too.
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    # /health is the only HTTP surface: no docs or schema routes.
    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)
    worker = settings.worker_enabled and bool(settings.database_url)
    app.state.supervisor = QueueSupervisor(settings) if worker else None
    app.state.health_service = HealthService(lambda: ping(settings.database_url), app.state.supervisor)
    register_error_handlers(app)
    app.include_router(health_router.router)
    return app


app = create_app()
