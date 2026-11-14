"""Fixtures: a located project, a fake scene and a fake solver."""

import json
import uuid
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import text

from app.services.simulations.scene_port import get_scene_service

EXAMPLES = Path(__file__).resolve().parents[5] / "docs/architecture/contracts/examples"
SCENE = json.loads((EXAMPLES / "scene.example.json").read_text())
BUILDING = {"id": str(uuid.uuid4()), "name": "B", "source": "draw", "height_m": 24.0,
            "footprint": [[-10, -15], [10, -15], [10, 15], [-10, 15]], "holes": []}
ROSE = {"calm_fraction": 0.04, "period_years": 10, "hours": 87600, "sectors": [
    {"center_deg": 22.5 * i, "frequency": 0.06, "mean_ms": 4.0, "p50_ms": 3.5,
     "p90_ms": 7.0, "max_ms": 12.0, "weibull_k": 2.0, "weibull_c_ms": 4.5}
    for i in range(16)]}


class FakeScene:
    """Return the normative example scene."""

    async def compile_for_alternative(self, user: Any, alternative_id: Any) -> dict:
        """Return a copy of scene.example.json."""
        return json.loads(json.dumps(SCENE))


async def sql(app: Any, query: str, **params: Any) -> list[Any]:
    """Run one statement in its own transaction and return all rows."""
    async with app.state.session_factory() as s:
        result = await s.execute(text(query), params)
        rows = result.all() if result.returns_rows else []
        await s.commit()
    return rows


@pytest.fixture
def fake_scene(app: Any) -> None:
    """Replace the scene service by the fake."""
    app.dependency_overrides[get_scene_service] = lambda: FakeScene()


@pytest.fixture
async def ready(app: Any, project: dict, fake_scene: None) -> dict[str, str]:
    """Locate the project, add a building and a manual wind."""
    pid = project["id"]
    await sql(app, "UPDATE projects SET lat=1.5, lon=2.5, elevation_m=100, "
              "air_density_kg_m3=1.225 WHERE id=:p", p=pid)
    await sql(app, "UPDATE geometries SET buildings=CAST(:b AS jsonb) WHERE project_id=:p",
              b=json.dumps([BUILDING]), p=pid)
    await sql(app, "UPDATE wind_climates SET manual_direction_deg=270, manual_u10_ms=10 "
              "WHERE project_id=:p", p=pid)
    alt = (await sql(app, "SELECT id FROM alternatives WHERE project_id=:p", p=pid))[0][0]
    return {"project_id": pid, "alternative_id": str(alt)}


@pytest.fixture
async def solver(app: Any) -> None:
    """Insert a fresh CPU solver node with a 16 GiB budget."""
    await sql(app, "INSERT INTO solver_nodes VALUES ('w','cpu',NULL,NULL,NULL,34359738368,"
              "17179869184,16,100,50,'1',now(),now())")


async def set_rose(app: Any, pid: str) -> None:
    """Switch a project's wind to an ERA5 rose."""
    await sql(app, "UPDATE wind_climates SET source='era5', rose=CAST(:r AS jsonb), "
              "cache_key='era5:syn:10y' WHERE project_id=:p", r=json.dumps(ROSE), p=pid)
