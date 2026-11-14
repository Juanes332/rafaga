"""Single list of every router the application serves."""

from fastapi import APIRouter

from app.routers.alternatives import alternatives_router
from app.routers.auth import auth_router
from app.routers.backgrounds import backgrounds_router
from app.routers.comfort import comfort_router
from app.routers.comparisons import comparisons_router
from app.routers.exports import exports_router
from app.routers.facades import facades_router
from app.routers.geo import geo_router
from app.routers.geometry import geometry_router
from app.routers.health import health_router
from app.routers.jobs import jobs_router
from app.routers.location import location_router
from app.routers.projects import project_router
from app.routers.reports import reports_router
from app.routers.results import results_router
from app.routers.scene import scene_router
from app.routers.settings import settings_router
from app.routers.shares import share_router
from app.routers.simulations import simulations_router
from app.routers.system import system_router
from app.routers.templates import templates_router
from app.routers.tiles import tiles_router
from app.routers.users import user_router
from app.routers.wind import wind_router


def all_routers() -> list[APIRouter]:
    """Return every router, public ones first."""
    return [
        health_router.router,
        auth_router.public_router,
        auth_router.router,
        system_router.router,
        user_router.router,
        project_router.router,
        share_router.router,
        location_router.router,
        geo_router.router,
        tiles_router.router,
        wind_router.router,
        geometry_router.router,
        backgrounds_router.router,
        alternatives_router.router,
        facades_router.router,
        scene_router.router,
        simulations_router.router,
        jobs_router.router,
        results_router.router,
        comfort_router.router,
        comparisons_router.router,
        exports_router.router,
        reports_router.router,
        settings_router.router,
        templates_router.router,
    ]
