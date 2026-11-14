"""Helpers shared by the alternatives, facades and scene tests."""

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from jsonschema import Draft202012Validator
from sqlalchemy import text

CONTRACTS = Path("/home/juanhez/Documents/juanhez/projects/rafaga/docs/architecture/contracts")
BUILDING_ID = "11111111-1111-4111-8111-111111111111"


def square_building(height: float = 24.0, building_id: str = BUILDING_ID) -> dict[str, Any]:
    """Return a 20 x 30 m building centred on the origin, CCW."""
    return {
        "id": building_id, "name": "B", "holes": [], "source": "draw",
        "footprint": [[-10, -15], [10, -15], [10, 15], [-10, 15]],
        "height_m": height, "missing_height": False,
    }


def scene_validator() -> Draft202012Validator:
    """Return a validator for contracts/scene.schema.json."""
    schema = json.loads((CONTRACTS / "scene.schema.json").read_text())
    return Draft202012Validator(schema)


def assert_valid_scene(scene: dict[str, Any]) -> None:
    """Fail with the first schema violation, if any."""
    errors = sorted(scene_validator().iter_errors(scene), key=lambda e: list(e.path))
    assert not errors, f"{list(errors[0].path)}: {errors[0].message}"


async def set_geometry(app: Any, project_id: str, buildings: list[dict[str, Any]], version: int = 3) -> None:
    """Store buildings on the project's geometry row."""
    async with app.state.session_factory() as s:
        await s.execute(
            text("UPDATE geometries SET buildings = CAST(:b AS jsonb), version = :v "
                 "WHERE project_id = :p"),
            {"b": json.dumps(buildings), "v": version, "p": project_id},
        )
        await s.commit()


async def base_alternative_id(client: Any, headers: dict[str, str], project_id: str) -> str:
    """Return the base alternative id through the API."""
    alts = (await client.get(f"/api/v1/projects/{project_id}/alternatives", headers=headers)).json()
    return next(a["id"] for a in alts if a["is_base"])


async def add_alternative(client: Any, headers: dict[str, str], project_id: str, name: str = "Alt") -> dict[str, Any]:
    """Create a derived alternative through the API."""
    r = await client.post(f"/api/v1/projects/{project_id}/alternatives", headers=headers, json={"name": name})
    assert r.status_code == 201, r.text
    return r.json()


async def insert_result(app: Any, project_id: str, alt_id: str, owner_id: str, k_mean: float) -> str:
    """Insert a completed study with one job and result; return the study id."""
    async with app.state.session_factory() as s:
        q = lambda sql, p: s.execute(text(sql), p)  # noqa: E731
        sid = str(uuid4())
        jid = str(uuid4())
        await q("INSERT INTO studies (id,project_id,alternative_id,owner_id,kind,request,dx_m) "
                "VALUES (:i,:p,:a,:o,'plan2d','{}',1)", {"i": sid, "p": project_id, "a": alt_id, "o": owner_id})
        await q("INSERT INTO jobs (id,study_id,project_id,owner_id,kind,lane,status,payload) "
                "VALUES (:j,:s,:p,:o,'plan2d','heavy','completed','{}')",
                {"j": jid, "s": sid, "p": project_id, "o": owner_id})
        await q("INSERT INTO results (job_id,study_id,project_id,alternative_id,kind,dx_m,device,"
                "output_grid,stats,convergence,comparability,comparability_key,dir,fields,images) "
                "VALUES (:j,:s,:p,:a,'plan2d',1,'cpu','{}',CAST(:st AS jsonb),'{}','{}','k','d','[]','[]')",
                {"j": jid, "s": sid, "p": project_id, "a": alt_id,
                 "st": json.dumps({"k_mean": k_mean, "k_max": 2, "k_p95": 1.5})})
        await s.commit()
    return sid
