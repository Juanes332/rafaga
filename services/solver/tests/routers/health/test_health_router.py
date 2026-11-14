"""GET /health contract (SOL-01)."""

from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.routers.health.health_router import get_health_service
from app.services.health.health_service import HealthService


class _Supervisor:
    caps = {"device": "gpu", "gpu_name": "Test GPU"}

    def lanes(self) -> dict:
        return {"heavy": {"busy": True, "job_id": "j-1"}, "light": {"busy": False}}


async def _get(service: HealthService):
    app = create_app()
    app.state.health_service = service
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        return await client.get("/health")


async def test_health_ok_reports_device_and_lanes() -> None:
    response = await _get(HealthService(lambda: True, _Supervisor()))
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "device": "gpu", "gpu_name": "Test GPU", "db": "ok",
                               "lanes": {"heavy": {"busy": True, "job_id": "j-1"},
                                         "light": {"busy": False}}}


async def test_health_is_503_when_db_unreachable() -> None:
    response = await _get(HealthService(lambda: False))
    assert response.status_code == 503
    assert response.json()["db"] == "down" and response.json()["status"] == "degraded"


async def test_health_is_the_only_route() -> None:
    from tests.conftest import all_route_paths

    paths = all_route_paths(create_app())
    assert paths == {"/health"}


async def test_unknown_route_answers_404_in_error_contract() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        response = await client.get("/jobs")
    assert response.status_code == 404 and response.json()["code"] == "http_error"
