"""PUT /projects/{id}/location."""

import httpx
import pytest
from httpx import AsyncClient

from app.services.geo.isa_density import isa_density
from tests.routers.geo.conftest import load  # noqa: F401

ELEV = "https://api.open-meteo.com/v1/elevation"
BODY = {"lat": 12.3456789, "lon": -45.6789012}


async def test_location_fetches_elevation_and_density(client: AsyncClient, architect, project, mocked) -> None:
    """Without elevation_m Open-Meteo is called; lat/lon keep 5 decimals."""
    mocked.get(ELEV).respond(200, json={"elevation": [500.0]})
    r = await client.put(f"/api/v1/projects/{project['id']}/location", headers=architect.headers, json=BODY)
    b = r.json()
    assert r.status_code == 200 and (b["lat"], b["lon"]) == (12.34568, -45.6789)
    assert b["elevation_m"] == 500.0 and b["elevation_source"] == "open_meteo"
    assert b["air_density_kg_m3"] == pytest.approx(isa_density(500.0))


async def test_location_manual_elevation_skips_network(client: AsyncClient, architect, project, mocked) -> None:
    """A given elevation is manual and makes zero outbound calls."""
    r = await client.put(f"/api/v1/projects/{project['id']}/location", headers=architect.headers,
                         json={**BODY, "elevation_m": 100})
    assert r.json()["elevation_source"] == "manual" and len(mocked.calls) == 0


async def test_location_out_of_range_is_422(client: AsyncClient, architect, project) -> None:
    """Latitude or longitude out of range."""
    for bad in ({"lat": 91, "lon": 0}, {"lat": 0, "lon": 181}):
        r = await client.put(f"/api/v1/projects/{project['id']}/location", headers=architect.headers, json=bad)
        assert r.status_code == 422 and r.json()["code"] == "coordinates_out_of_range"


async def test_location_malformed_payload_is_422(client: AsyncClient, architect, project) -> None:
    """Missing lon is a validation error."""
    r = await client.put(f"/api/v1/projects/{project['id']}/location", headers=architect.headers, json={"lat": 1})
    assert r.status_code == 422 and r.json()["code"] == "validation_error"


async def test_location_elevation_failure_is_503_with_hint(client: AsyncClient, architect, project, mocked) -> None:
    """Upstream failure leaves the project unchanged."""
    mocked.get(ELEV).mock(side_effect=httpx.ConnectError("x"))
    r = await client.put(f"/api/v1/projects/{project['id']}/location", headers=architect.headers, json=BODY)
    after = (await client.get(f"/api/v1/projects/{project['id']}", headers=architect.headers)).json()
    assert r.status_code == 503 and r.json()["code"] == "elevation_unavailable" and r.json()["hint"]
    assert after["lat"] is None


async def test_location_auth_foreign_and_reviewer(client: AsyncClient, architect, other_architect, reviewer, project) -> None:
    """401 anonymous, byte-identical 404 foreign/missing, 403 shared reviewer."""
    url = f"/api/v1/projects/{project['id']}/location"
    body = {**BODY, "elevation_m": 1}
    assert (await client.put(url, json=body)).status_code == 401
    foreign = await client.put(url, headers=other_architect.headers, json=body)
    missing = await client.put("/api/v1/projects/00000000-0000-4000-8000-0000000000aa/location",
                               headers=other_architect.headers, json=body)
    assert foreign.status_code == 404 and foreign.content == missing.content
    await client.put(f"/api/v1/projects/{project['id']}/shares/{reviewer.id}", headers=architect.headers)
    denied = await client.put(url, headers=reviewer.headers, json=body)
    assert denied.status_code == 403
