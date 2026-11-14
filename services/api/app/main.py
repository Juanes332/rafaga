"""Application entry point and FastAPI factory."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.configs.config import get_settings
from app.core.database.database import build_engine, build_session_factory
from app.core.errors.error_handlers import register_error_handlers
from app.routers.router_registry import all_routers
from app.security.rate_limit.rate_limiter import register_rate_limiting
from app.services.auth.admin_seed_service import seed_admin
from app.services.jobs.retention_service import retention_loop

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Seed the admin, run the daily purge, dispose the engine on exit."""
    settings = get_settings()
    try:
        async with app.state.session_factory() as session:
            await seed_admin(session, settings)
    except Exception:  # noqa: BLE001 - /health must still report the db state
        logger.exception("admin_seed_failed")
    purge = asyncio.create_task(retention_loop(app.state.session_factory, settings))
    yield
    purge.cancel()
    await app.state.engine.dispose()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )
    # Owned by the app, not by the module: tests build independent apps.
    app.state.engine = build_engine(settings.database_url)
    app.state.session_factory = build_session_factory(app.state.engine)
    register_rate_limiting(app)
    register_error_handlers(app)
    if settings.origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.origins,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["Content-Disposition", "X-Field-Shape", "X-Field-Dtype", "Retry-After"],
        )
    for router in all_routers():
        app.include_router(router)
    return app


app = create_app()
