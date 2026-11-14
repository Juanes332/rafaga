"""Geo endpoints: search, elevation, terrain categories."""

import httpx
import pytest
from httpx import AsyncClient

from app.services.geo.isa_density import isa_density
from tests.routers.geo.conftest import load

GEO = "https://geocoding-api.open-meteo.com/v1/search"
ELEV = "https://api.open-meteo.com/v1/elevation"


async def test_search_returns_matches_and_caches(client: AsyncClient, architect, mocked) -> None:
    """Second identical search makes zero outbound calls."""
    route = mocked.get(GEO).respond(200, json=load("open_meteo_geocode.json"))
    r = await client.get("/api/v1/geo/search", params={"q": "Sampletown"}, headers=architect.headers)
    again = await client.get("/api/v1/geo/search", params={"q": "sampletown"}, headers=architect.headers)
    assert r.status_code == 200 and r.json()[0]["name"] == "Sampletown"
    assert r.json()[0]["lat"] == 10.12345 and r.json()[1]["elevation_m"] is None
    assert again.json() == r.json() and route.call_count == 1
    assert route.calls[0].request.url.params["language"] == "es"


async def test_search_validation_and_auth(client: AsyncClient, architect) -> None:
    """Short q is 422; no token is 401."""
    short = await client.get("/api/v1/geo/search", params={"q": "a"}, headers=architect.headers)
    anon = await client.get("/api/v1/geo/search", params={"q": "abc"})
    assert short.status_code == 422 and anon.status_code == 401


async def test_search_upstream_down_is_503(client: AsyncClient, architect, mocked) -> None:
    """No upstream and no cache answers geocoding_unavailable."""
    mocked.get(GEO).mock(side_effect=httpx.ConnectError("down"))
    r = await client.get("/api/v1/geo/search", params={"q": "Nowhere"}, headers=architect.headers)
    assert r.status_code == 503 and r.json()["code"] == "geocoding_unavailable"


async def test_elevation_rounds_coordinates_and_caches(client: AsyncClient, architect, mocked) -> None:
    """Only 4-decimal coordinates leave; the second call is cached."""
    route = mocked.get(ELEV).respond(200, json=load("open_meteo_elevation.json"))
    p = {"lat": 10.123456789, "lon": -20.987654321}
    r = await client.get("/api/v1/geo/elevation", params=p, headers=architect.headers)
    await client.get("/api/v1/geo/elevation", params=p, headers=architect.headers)
    body = r.json()
    assert body["elevation_m"] == 812.0 and body["source"] == "open_meteo"
    assert body["air_density_kg_m3"] == pytest.approx(isa_density(812.0))
    assert route.call_count == 1
    sent = route.calls[0].request.url.params
    assert (sent["latitude"], sent["longitude"]) == ("10.1235", "-20.9877")


async def test_elevation_out_of_range_is_422(client: AsyncClient, architect) -> None:
    """Out-of-range coordinates carry their own code."""
    r = await client.get("/api/v1/geo/elevation", params={"lat": 91, "lon": 0}, headers=architect.headers)
    assert r.status_code == 422 and r.json()["code"] == "coordinates_out_of_range"


async def test_elevation_upstream_failure_is_503_with_hint(client: AsyncClient, architect, mocked) -> None:
    """Upstream failure hints at manual entry."""
    mocked.get(ELEV).respond(500)
    r = await client.get("/api/v1/geo/elevation", params={"lat": 1, "lon": 2}, headers=architect.headers)
    assert r.status_code == 503 and r.json()["code"] == "elevation_unavailable" and r.json()["hint"]


async def test_terrain_categories(client: AsyncClient, architect) -> None:
    """Five categories, urban flagged default."""
    r = await client.get("/api/v1/terrain-categories", headers=architect.headers)
    cats = {c["key"]: c for c in r.json()}
    assert list(cats) == ["open_sea", "open", "suburban", "urban", "dense_urban"]
    assert cats["dense_urban"]["z0_m"] == 2.0
    assert [k for k, c in cats.items() if c["default"]] == ["urban"]
    assert (await client.get("/api/v1/terrain-categories")).status_code == 401


def test_isa_density_sea_level_and_altitude() -> None:
    """BR-06 anchors: 1.225 at sea level, lower with altitude."""
    assert isa_density(0) == pytest.approx(1.225)
    assert isa_density(2000) == pytest.approx(1.0066, abs=1e-3)
