"""POST /simulations/estimate."""

from httpx import AsyncClient

from tests.routers.simulations.conftest import sql

URL = "/api/v1/simulations/estimate"


def body(ready: dict, **extra) -> dict:  # noqa: ANN003
    """Return a valid estimate body."""
    return {"alternative_id": ready["alternative_id"], "kind": "plan2d",
            "directions_deg": [270], "dx_m": 1.0, **extra}


async def test_estimate_matches_the_contract_memory(client: AsyncClient, architect, ready, solver) -> None:  # noqa: ANN001
    """Memory equals the contract example and the grid is returned."""
    r = await client.post(URL, headers=architect.headers, json=body(ready))
    j = r.json()
    assert r.status_code == 200
    assert j["memory_bytes"] == 552554112 and j["fits"] and j["device"] == "cpu"
    assert j["proposed_dx_m"] is None and j["grid"]["output"]["nx"] == 136
    assert j["eta_seconds"] > 0


async def test_estimate_without_solver_is_honest(client: AsyncClient, architect, ready) -> None:  # noqa: ANN001
    """No solver row: fits false, no invented budget."""
    j = (await client.post(URL, headers=architect.headers, json=body(ready))).json()
    assert (j["fits"], j["budget_bytes"], j["rejected_reason"]) == (False, 0, "solver_offline")


async def test_estimate_proposes_coarser_dx(client: AsyncClient, architect, ready, solver, app) -> None:  # noqa: ANN001
    """A small budget yields a proposal that is a 0.25 m multiple."""
    await sql(app, "UPDATE solver_nodes SET ram_budget_bytes=560000000")
    j = (await client.post(URL, headers=architect.headers, json=body(ready, dx_m=0.5))).json()
    assert not j["fits"] and j["proposed_dx_m"] % 0.25 == 0 and j["proposed_dx_m"] > 0.5


async def test_estimate_location_missing_and_validation_and_auth(
    client: AsyncClient, architect, ready
) -> None:  # noqa: ANN001
    """422 on bad dx or a section without a line, 401 anonymous."""
    bad = await client.post(URL, headers=architect.headers, json=body(ready, dx_m=0.1))
    anon = await client.post(URL, json=body(ready))
    assert bad.status_code == 422 and bad.json()["code"] == "validation_error"
    assert anon.status_code == 401
    section = await client.post(URL, headers=architect.headers,
                                json={**body(ready), "kind": "section2d"})
    assert section.status_code == 422


async def test_estimate_requires_location(client: AsyncClient, architect, ready, app) -> None:  # noqa: ANN001
    """A project whose location was cleared answers 409 location_missing."""
    await sql(app, "UPDATE projects SET lat=NULL, lon=NULL")
    r = await client.post(URL, headers=architect.headers, json=body(ready))
    assert (r.status_code, r.json()["code"]) == (409, "location_missing")


async def test_estimate_foreign_alternative_equals_missing(
    client: AsyncClient, other_architect, ready
) -> None:  # noqa: ANN001
    """A foreign alternative id answers the same bytes as a random one."""
    foreign = await client.post(URL, headers=other_architect.headers, json=body(ready))
    missing = await client.post(URL, headers=other_architect.headers, json={
        **body(ready), "alternative_id": "00000000-0000-4000-8000-0000000000aa"})
    assert foreign.status_code == missing.status_code == 404
    assert foreign.content == missing.content
