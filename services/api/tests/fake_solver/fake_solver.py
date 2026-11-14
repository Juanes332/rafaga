"""Fake solver: writes volume files and rows the way the real one does."""

import hashlib
import io
import json
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image
from sqlalchemy import text

from app.configs.config import get_settings

DISCLAIMER_FIELDS = ("K", "ux", "uy", "speed")


def _png() -> bytes:
    """Return a tiny valid PNG."""
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), (10, 20, 30)).save(buf, "PNG")
    return buf.getvalue()


def canonical_hash(data: dict[str, Any]) -> str:
    """Return the sha256 of the canonical JSON of the data."""
    raw = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


class FakeSolver:
    """Insert studies, jobs, results and comfort rows plus their files."""

    def __init__(self, app: Any) -> None:
        """Bind the app whose database and data_dir to fill."""
        self.app = app
        self.data = Path(get_settings().data_dir)

    async def _exec(self, sql: str, params: dict[str, Any]) -> Any:
        async with self.app.state.session_factory() as s:
            row = (await s.execute(text(sql), params)).first()
            await s.commit()
            return row[0] if row else None

    async def base_alt(self, project_id: str) -> str:
        """Return the base alternative id of a project."""
        return str(await self._exec(
            "SELECT id FROM alternatives WHERE project_id=:p AND is_base", {"p": project_id}))

    async def study(self, project_id: str, owner_id: str, *, kind: str = "plan2d",
                    template: dict[str, Any] | None = None, alt: str | None = None) -> str:
        """Insert a study row and return its id."""
        alt = alt or await self.base_alt(project_id)
        return str(await self._exec(
            "INSERT INTO studies (project_id, alternative_id, owner_id, kind, request, dx_m,"
            " aggregate_template) VALUES (:p,:a,:o,:k,CAST(:r AS jsonb),1.0,"
            "CAST(:t AS jsonb)) RETURNING id",
            {"p": project_id, "a": alt, "o": owner_id, "k": kind,
             "r": json.dumps({"directions_deg": [270.0]}),
             "t": json.dumps(template) if template else None}))

    async def job(self, project_id: str, owner_id: str, study_id: str | None, *, kind: str,
                  status: str = "completed", payload: dict[str, Any] | None = None,
                  direction: float | None = None, lane: str = "heavy") -> str:
        """Insert a job row and return its id."""
        return str(await self._exec(
            "INSERT INTO jobs (study_id, project_id, owner_id, kind, lane, status, payload,"
            " direction_deg, progress) VALUES (:s,:p,:o,:k,:l,:st,CAST(:pl AS jsonb),:d,"
            "CASE WHEN :st='completed' THEN 1 ELSE 0 END) RETURNING id",
            {"s": study_id, "p": project_id, "o": owner_id, "k": kind, "l": lane, "st": status,
             "pl": json.dumps(payload or {"scene": {"solids": []}}), "d": direction}))

    async def result(self, project_id: str, owner_id: str, study_id: str, *,
                     k: np.ndarray | None = None, direction: float = 270.0, dx: float = 1.0,
                     z0: float = 1.0, kind: str = "plan2d", ha: float = 1.5,
                     scene: dict[str, Any] | None = None,
                     warnings: list[Any] | None = None) -> dict[str, Any]:
        """Write result files and rows; return ids and the field array."""
        k = np.full((6, 8), 0.8, dtype="<f4") if k is None else k.astype("<f4")
        ny, nx = k.shape
        grid = {"frame": "plan", "origin_x": -4.0, "origin_y": -3.0, "dx_m": dx, "nx": nx, "ny": ny}
        payload = {"scene": scene or {"solids": [], "porous": []}}
        job_id = await self.job(project_id, owner_id, study_id, kind=kind, direction=direction,
                                payload=payload)
        rel = f"results/{project_id}/{study_id}/{job_id}"
        files = self._write(rel, k, kind)
        comp = {"kind": kind, "direction_deg": direction, "z0_m": z0, "uref_za_ms": 3.82,
                "dx_m": dx, "output_grid": grid, "analysis_height_m": ha, "section": None}
        fluid = float(np.isfinite(k).sum() * dx * dx)
        stats = {"k_mean": float(np.nanmean(k)), "k_max": float(np.nanmax(k)),
                 "k_p95": float(np.nanpercentile(k, 95)), "fluid_area_m2": fluid}
        conv = {"converged": True, "flow_through_steps": 100, "rel_change_last": 0.005}
        alt = await self.base_alt(project_id)
        rid = await self._exec(
            "INSERT INTO results (job_id, study_id, project_id, alternative_id, kind, direction_deg,"
            " dx_m, device, output_grid, stats, convergence, comparability, comparability_key, dir,"
            " fields, images, warnings) VALUES (:j,:s,:p,:a,:k,:d,:dx,'cpu',CAST(:g AS jsonb),"
            "CAST(:st AS jsonb),CAST(:cv AS jsonb),CAST(:cp AS jsonb),:ck,:dir,CAST(:f AS jsonb),"
            "CAST(:im AS jsonb),CAST(:w AS jsonb)) RETURNING id",
            {"j": job_id, "s": study_id, "p": project_id, "a": alt, "k": kind, "d": direction,
             "dx": dx, "g": json.dumps(grid), "st": json.dumps(stats), "cv": json.dumps(conv),
             "cp": json.dumps(comp), "ck": canonical_hash(comp), "dir": rel,
             "f": json.dumps(files[0]), "im": json.dumps(files[1]),
             "w": json.dumps(warnings or [])})
        return {"id": str(rid), "job_id": job_id, "dir": rel, "k": k}

    def _write(self, rel: str, k: np.ndarray, kind: str) -> tuple[list[Any], list[Any]]:
        base = self.data / rel
        (base / "fields").mkdir(parents=True)
        (base / "images").mkdir()
        fields = []
        arrays = {"K": k, "ux": k * 0.5, "uy": k * 0.25, "speed": k * 3.0}
        for name, arr in arrays.items():
            (base / f"fields/{name}.f32").write_bytes(arr.astype("<f4").tobytes())
            fields.append({"name": name, "file": f"fields/{name}.f32", "dtype": "float32",
                           "shape": list(arr.shape)})
        mask = np.zeros(k.shape, dtype="u1")
        mask[~np.isfinite(k)] = 1
        (base / "fields/mask.u8").write_bytes(mask.tobytes())
        fields.append({"name": "mask", "file": "fields/mask.u8", "dtype": "uint8",
                       "shape": list(k.shape)})
        np.savez(base / "fields.npz", mask=mask, **arrays)
        images = []
        names = ("k", "speed", "zones") + (("delta", "slice_xz") if kind == "volume3d" else ())
        for name in names:
            (base / f"images/{name}.png").write_bytes(_png())
            images.append({"name": name, "file": f"images/{name}.png"})
        if kind == "volume3d":
            (base / "volume").mkdir()
            (base / "volume/slice_xz.f32").write_bytes(k.tobytes())
            viewer = {"slices": [{"name": "xz", "plane": "xz", "extents": [0, 1, 0, 1],
                                  "field": "slice_xz", "shape": list(k.shape)}],
                      "streamlines": [[[0, 0, 0], [1, 1, 1]]], "frame": "local_enu"}
            (base / "volume/viewer3d.json").write_text(json.dumps(viewer))
        return fields, images

    async def comfort(self, study_id: str, job_id: str, lawson_hash: str, *,
                      lawson: dict[str, Any] | None = None) -> str:
        """Insert a completed comfort_results row."""
        return str(await self._exec(
            "INSERT INTO comfort_results (study_id, job_id, lawson_hash, lawson, coverage, partial,"
            " class_areas, safety_areas, dir, fields, images) VALUES (:s,:j,:h,CAST(:l AS jsonb),"
            "0.9,true,CAST(:ca AS jsonb),CAST(:sa AS jsonb),'results/x',CAST(:f AS jsonb),"
            "CAST(:i AS jsonb)) RETURNING id",
            {"s": study_id, "j": job_id, "h": lawson_hash, "l": json.dumps(lawson or {}),
             "ca": json.dumps([{"class": "A", "area_m2": 10.0, "percent": 50.0}]),
             "sa": json.dumps([{"label": "general_public", "area_m2": 1.0, "percent": 5.0}]),
             "f": json.dumps([{"name": "lawson_class", "file": "fields/lawson_class.u8"}]),
             "i": json.dumps([{"name": "lawson", "file": "images/lawson.png"}])}))


@pytest.fixture
def fake_solver(app: Any) -> FakeSolver:
    """Return a fake solver bound to the test app."""
    return FakeSolver(app)


def new_id() -> str:
    """Return a random uuid string."""
    return str(uuid.uuid4())
