"""Gust-factor floor semantics in the Lawson manifest and on a volume3d result (BL-01)."""

import copy
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from app.configs.config import Settings
from app.services.comfort.aggregate_service import run_aggregate
from app.services.comfort.lawson_model import exceedance, gust_factor
from app.services.simulation.heavy_job_service import run_heavy_job
from tests.support.contracts import example
from tests.support.payload_factory import plan_payload
from tests.support.result_store import aggregate_payload

# Smallest resolved I for which (1 + 3 I) / 1.85 exceeds 1 (the GEM exceeds the mean).
TI_GUST_ONSET = (1.85 - 1.0) / 3.0


def _manifest(settings: Settings, row: dict) -> dict:
    return json.loads((Path(settings.data_dir) / row["dir"] / "manifest.json").read_text())


def test_manifest_states_the_g_floor_applies_to_cells_without_valid_ti(result_store) -> None:
    """plan2d results carry no resolved ti: every fluid cell uses the default and the floor."""
    row = run_aggregate(aggregate_payload(result_store), result_store.settings)
    gust = _manifest(result_store.settings, row)["gust_factor"]
    assert gust["floor"] == 1.0
    assert gust["floor_applies_to"] == "cells_without_valid_ti"
    assert gust["resolved_ti_cells"] == 0
    assert gust["default_ti_cells"] > 0
    assert gust["default_ti"] == pytest.approx(0.25)


@pytest.fixture(scope="module")
def volume_store(tmp_path_factory):
    """Run one coarse CPU volume3d job (real resolved ti) and return (settings, dir, grid)."""
    root = tmp_path_factory.mktemp("vol")
    settings = Settings(data_dir=str(root), rafaga_device="cpu")
    raw = plan_payload(dx=6.0, wind_from=270.0, device="cpu", kind="volume3d")
    raw["output_dir"] = "results/p/s/vol"
    manifest = run_heavy_job(raw, "vol", settings, lambda *_: False)
    return settings, manifest["dir"], manifest["output_grid"]


@pytest.mark.slow
def test_lawson_gem_exceeds_u_where_resolved_ti_is_above_the_gust_onset(volume_store) -> None:
    """On a real volume3d result GEM > U exactly where resolved ti passes the gust onset."""
    settings, folder, grid = volume_store
    fdir = Path(settings.data_dir) / folder
    man = json.loads((fdir / "manifest.json").read_text())
    shape = next(f["shape"] for f in man["fields"] if f["name"] == "ti")
    ti = np.fromfile(fdir / "fields/ti.f32", dtype="<f4").reshape(shape)
    assert (ti > 0).any() and np.isfinite(ti).any()

    g = gust_factor(np.where(np.isfinite(ti), ti, 0.0))
    resolved = np.isfinite(ti) & (ti > TI_GUST_ONSET)
    assert resolved.any(), "volume3d produced no gusty cells; GEM test would be vacuous"
    assert (g[resolved] > 1.0).all()
    assert (g[np.isfinite(ti) & (ti <= TI_GUST_ONSET)] == 1.0).all()

    sector = {"frequency": 1.0, "weibull_k": 2.0, "weibull_c_ms": 6.0, "T": 1.0,
              "K": np.ones(shape)}
    p_gusty = exceedance(5.0, [sector | {"G": g}], 1.0)
    p_floor = exceedance(5.0, [sector | {"G": np.ones(shape)}], 1.0)
    assert (p_gusty[resolved] > p_floor[resolved]).all()


@pytest.mark.slow
def test_aggregate_over_volume3d_result_reports_resolved_cells(volume_store) -> None:
    """The aggregate manifest counts resolved ti cells and keeps the floor statement."""
    settings, folder, grid = volume_store
    raw = copy.deepcopy(example("job.aggregate.example"))
    raw["result_refs"] = [{"result_id": "r0", "wind_from_deg": 270.0, "dir": folder}]
    raw["output_grid"] = grid
    gust = _manifest(settings, run_aggregate(raw, settings))["gust_factor"]
    assert gust["resolved_ti_cells"] > 0
    assert gust["floor_applies_to"] == "cells_without_valid_ti"
