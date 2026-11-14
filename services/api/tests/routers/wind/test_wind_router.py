"""Wind endpoints."""

import math

import httpx
import pytest
from httpx import AsyncClient

from tests.routers.wind.conftest import synthetic_hourly

ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"


async def _located(client, actor, project) -> str:  # noqa: ANN001
    url = f"/api/v1/projects/{project['id']}"
    await client.put(f"{url}/location", headers=actor.headers, json={"lat": 33.33, "lon": 44.44, "elevation_m": 200})
    return url


async def test_new_project_wind_defaults(client: AsyncClient, architect, project) -> None:
    """Rose null, urban z0 1.0, no manual wind."""
    r = await client.get(f"/api/v1/projects/{project['id']}/wind", headers=architect.headers)
    b = r.json()
    assert r.status_code == 200 and b["rose"] is None and b["z0_m"] == 1.0
    assert b["terrain_category"] == "urban" and b["manual_u10_ms"] is None and b["ustar_ms"] is None
    assert b["from_cache"] is False


async def test_patch_manual_wind_computes_ustar(client: AsyncClient, architect, project) -> None:
    """u* follows kappa U10 / ln((10+z0)/z0)."""
    url = f"/api/v1/projects/{project['id']}/wind"
    r = await client.patch(url, headers=architect.headers, json={"manual_u10_ms": 10, "manual_direction_deg": 270})
    assert r.json()["ustar_ms"] == pytest.approx(0.41 * 10 / math.log(11.0))


async def test_patch_category_sets_z0_and_explicit_z0_wins(client: AsyncClient, architect, project) -> None:
    """Category resolves z0 unless z0_m is also given."""
    url = f"/api/v1/projects/{project['id']}/wind"
    a = await client.patch(url, headers=architect.headers, json={"terrain_category": "suburban"})
    b = await client.patch(url, headers=architect.headers, json={"terrain_category": "open", "z0_m": 0.05})
    assert a.json()["z0_m"] == 0.3 and b.json()["z0_m"] == 0.05


async def test_patch_validation_and_rose_missing(client: AsyncClient, architect, project) -> None:
    """Ranges are enforced; era5 without a rose is 409."""
    url = f"/api/v1/projects/{project['id']}/wind"
    for bad in ({"manual_u10_ms": 0.1}, {"manual_u10_ms": 61}, {"manual_direction_deg": 361}, {"z0_m": 0}, {"z0_m": 3.1}):
        assert (await client.patch(url, headers=architect.headers, json=bad)).status_code == 422
    r = await client.patch(url, headers=architect.headers, json={"source": "era5"})
    assert r.status_code == 409 and r.json()["code"] == "rose_missing"


async def test_era5_requires_location(client: AsyncClient, architect, project, mocked) -> None:
    """Unplaced project is 409 location_missing."""
    r = await client.post(f"/api/v1/projects/{project['id']}/wind/era5", headers=architect.headers, json={})
    assert r.status_code == 409 and r.json()["code"] == "location_missing"


async def test_era5_builds_rose_and_second_call_hits_cache(client: AsyncClient, architect, project, mocked) -> None:
    """16 sectors summing to 1; identical request makes zero outbound calls."""
    url = await _located(client, architect, project)
    route = mocked.get(ARCHIVE).respond(200, json=synthetic_hourly())
    r = await client.post(f"{url}/wind/era5", headers=architect.headers, json={"years": 1})
    b = r.json()
    assert r.status_code == 200 and b["source"] == "era5" and b["from_cache"] is False
    assert len(b["rose"]["sectors"]) == 16 and b["fetched_at"] and b["air_density_kg_m3"]
    total = sum(s["frequency"] for s in b["rose"]["sectors"]) + b["rose"]["calm_fraction"]
    assert total == pytest.approx(1.0, abs=1e-3)
    assert {"mean_ms", "p50_ms", "p90_ms", "max_ms", "weibull_k", "weibull_c_ms"} <= set(b["rose"]["sectors"][0])
    sent = route.calls[0].request.url.params
    assert (sent["latitude"], sent["longitude"]) == ("33.3", "44.4")
    again = await client.post(f"{url}/wind/era5", headers=architect.headers, json={"years": 1})
    assert route.call_count == 1 and again.json()["from_cache"] is True
    stored = await client.get(f"{url}/wind", headers=architect.headers)
    assert stored.json()["rose"] == b["rose"] and stored.json()["period_years"] == 1


async def test_era5_unavailable_without_network_or_cache(client: AsyncClient, architect, project, mocked) -> None:
    """503 era5_unavailable with a manual-entry hint."""
    url = await _located(client, architect, project)
    mocked.get(ARCHIVE).mock(side_effect=httpx.ConnectError("offline"))
    r = await client.post(f"{url}/wind/era5", headers=architect.headers, json={})
    assert r.status_code == 503 and r.json()["code"] == "era5_unavailable" and r.json()["hint"]


async def test_wind_privacy_and_roles(client: AsyncClient, architect, other_architect, reviewer, project) -> None:
    """401 anonymous; foreign==missing; reviewer reads but cannot write."""
    url = f"/api/v1/projects/{project['id']}/wind"
    assert (await client.get(url)).status_code == 401
    foreign = await client.get(url, headers=other_architect.headers)
    missing = await client.get("/api/v1/projects/00000000-0000-4000-8000-0000000000aa/wind", headers=other_architect.headers)
    assert foreign.status_code == 404 and foreign.content == missing.content
    await client.put(f"/api/v1/projects/{project['id']}/shares/{reviewer.id}", headers=architect.headers)
    assert (await client.get(url, headers=reviewer.headers)).status_code == 200
    assert (await client.patch(url, headers=reviewer.headers, json={"z0_m": 0.3})).status_code == 403
    assert (await client.post(f"{url}/era5", headers=reviewer.headers, json={})).status_code == 403
