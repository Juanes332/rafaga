"""The one error contract, wired inside the factory."""

from fastapi import APIRouter
from httpx import ASGITransport, AsyncClient

from app.core.errors.error_contract import ConflictError
from app.main import create_app


def _app():  # noqa: ANN202
    app = create_app()
    r = APIRouter()

    @r.get("/boom")
    async def boom() -> None:
        raise RuntimeError("postgresql://user:secret@db/x")

    @r.get("/conflict")
    async def conflict() -> None:
        raise ConflictError("state", details={"k": 1}, hint="fix it")

    app.include_router(r)
    return app


async def test_unexpected_exception_is_500_without_leaking() -> None:
    """The catch-all hides the exception message."""
    app = _app()
    async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://t") as c:
        r = await c.get("/boom")
    assert r.status_code == 500 and "secret" not in r.text
    assert r.json() == {"code": "internal_error", "message": "The request could not be completed."}


async def test_app_error_maps_status_code_details_and_hint() -> None:
    """Domain errors keep their own status and optional fields."""
    async with AsyncClient(transport=ASGITransport(app=_app()), base_url="http://t") as c:
        r = await c.get("/conflict")
    assert r.status_code == 409
    assert r.json() == {"code": "conflict", "message": "state", "details": {"k": 1}, "hint": "fix it"}


async def test_unknown_route_uses_the_same_shape() -> None:
    """Framework 404s are reshaped into ErrorBody."""
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://t") as c:
        r = await c.get("/nope")
    assert r.status_code == 404 and r.json()["code"] == "http_error"
