"""Every outward-facing route is guarded; only listed ones are public.

STRUCTURAL: walks the registered routes, so an unguarded route added
tomorrow fails on the day it lands.
"""

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.main import create_app

PUBLIC_PATHS = {
    "/health",
    "/api/v1/auth/setup-status",
    "/api/v1/auth/setup",
    "/api/v1/auth/login",
}
INTERNAL_PREFIX = "/internal"


def api_routes(app: FastAPI) -> list[APIRoute]:
    """Return every APIRoute the app serves, nested ones included."""
    routes: list[APIRoute] = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append(route)
        inner = getattr(route, "original_router", None)
        if inner is not None:
            routes.extend(r for r in inner.routes if isinstance(r, APIRoute))
    return routes


def guard_names(route: APIRoute) -> set[str]:
    """Return the names of every dependency the route resolves."""
    return {d.call.__name__ for d in route.dependant.dependencies if d.call is not None}


def test_every_public_route_resolves_a_guard() -> None:
    """No route outside PUBLIC_PATHS answers without proving who calls."""
    unguarded = [
        r.path for r in api_routes(create_app())
        if r.path not in PUBLIC_PATHS
        and not r.path.startswith(INTERNAL_PREFIX)
        and not any(n.startswith("require_") for n in guard_names(r))
    ]
    assert unguarded == []


def test_every_guarded_route_spends_the_principal_budget() -> None:
    """Tier 2 must follow the guard on every guarded route."""
    missing = [
        r.path for r in api_routes(create_app())
        if r.path not in PUBLIC_PATHS
        and not ({"enforce_principal_rate_limit", "enforce_tiles_rate_limit"} & guard_names(r))
    ]
    assert missing == []


def test_public_routes_are_exactly_the_agreed_ones() -> None:
    """The unguarded set must not grow silently."""
    open_paths = {
        r.path for r in api_routes(create_app())
        if not any(n.startswith("require_") for n in guard_names(r))
    }
    assert open_paths == PUBLIC_PATHS
