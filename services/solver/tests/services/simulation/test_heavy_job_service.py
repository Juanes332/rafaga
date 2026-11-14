"""End-to-end heavy jobs on coarse grids (SOL-07, SOL-08, SOL-09, SOL-11, SOL-19)."""

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from app.configs.config import Settings
from app.core.errors.solver_errors import MeshTooLargeError
from app.services.simulation.heavy_job_service import run_heavy_job
from tests.support.contracts import example
from tests.support.gpu_marks import HAS_GPU
from tests.support.payload_factory import plan_payload, section_payload

FAST_DEVICE = "gpu" if HAS_GPU else "cpu"


def _run(tmp_path: Path, raw: dict) -> tuple[dict, Path]:
    raw["output_dir"] = "results/p/s/j"
    settings = Settings(data_dir=str(tmp_path), rafaga_device="auto")
    manifest = run_heavy_job(raw, "j", settings, lambda *_: False)
    return manifest, tmp_path / "results/p/s/j"


def test_plan2d_writes_contract_fields_and_manifest(result_store) -> None:
    folder = Path(result_store.settings.data_dir) / result_store.dirs[270.0]
    manifest = json.loads((folder / "manifest.json").read_text())
    assert set(example("result-manifest.example")) <= set(manifest)
    names = [f["name"] for f in manifest["fields"]]
    assert names == ["K", "ux", "uy", "speed", "ti", "mask"]
    shape = [manifest["output_grid"]["ny"], manifest["output_grid"]["nx"]]
    k = np.fromfile(folder / "fields/K.f32", dtype="<f4").reshape(shape)
    mask = np.fromfile(folder / "fields/mask.u8", dtype=np.uint8).reshape(shape)
    assert np.isnan(k[mask == 1]).all() and np.isfinite(k[mask != 1]).all()
    assert [i["name"] for i in manifest["images"]] == ["k", "speed", "zones"]
    assert Image.open(folder / "images/k.png").info["dpi"][0] == pytest.approx(150, abs=1)
    assert not folder.with_name(folder.name + ".tmp").exists()


def test_plan2d_wake_is_slower_than_free_stream(result_store) -> None:
    folder = Path(result_store.settings.data_dir) / result_store.dirs[270.0]
    stats = json.loads((folder / "manifest.json").read_text())["stats"]
    assert stats["k_max"] > 1.1 and 0.5 < stats["k_mean"] < 1.1


def test_section2d_writes_section_fields(tmp_path) -> None:
    manifest, folder = _run(tmp_path, section_payload(dx=6.0, device=FAST_DEVICE))
    assert [f["name"] for f in manifest["fields"]] == ["K", "us", "uz", "speed", "mask"]
    assert manifest["fields"][0]["shape"] == [manifest["output_grid"]["nz"], manifest["output_grid"]["ns"]]


def test_volume3d_writes_slice_viewer_and_ti(tmp_path) -> None:
    raw = plan_payload(dx=8.0, kind="volume3d", device=FAST_DEVICE)
    manifest, folder = _run(tmp_path, raw)
    assert [f["name"] for f in manifest["fields"]] == ["K", "ux", "uy", "uz", "speed", "ti", "mask"]
    viewer = json.loads((folder / "volume/viewer3d.json").read_text())
    assert viewer["frame"] == "local_enu" and len(viewer["slices"]) == 2
    assert 0 < len(viewer["streamlines"]) <= 400
    assert all(len(line) <= 500 for line in viewer["streamlines"])
    nz, nx = viewer["slices"][0]["shape"]
    assert (folder / "volume/slice_xz.f32").stat().st_size == nz * nx * 4


def test_oversized_mesh_fails_fast_with_proposed_dx(tmp_path) -> None:
    raw = plan_payload(dx=4.0, kind="volume3d", device="cpu")
    raw["grid"]["sim"]["nz"] = 4000
    with pytest.raises(MeshTooLargeError) as err:
        _run(tmp_path, raw)
    assert err.value.details["proposed_dx_m"] > 4.0
    assert not (tmp_path / "results/p/s/j.tmp").exists()


def test_volume3d_with_a_low_top_runs_on_a_raised_domain(tmp_path) -> None:
    raw = plan_payload(dx=8.0, kind="volume3d", device=FAST_DEVICE)
    raw["grid"]["sim"]["nz"] = 8  # 64 m = 2.7 H
    manifest, folder = _run(tmp_path, raw)
    assert folder.is_dir()
    viewer = json.loads((folder / "volume/viewer3d.json").read_text())
    assert viewer["slices"][0]["shape"][0] == 15  # ceil(5 x 24 m / 8 m)
    assert viewer["slices"][0]["extents"][5] >= 5 * 24.0
    assert "domain_top_capped" not in {w["code"] for w in manifest["warnings"]}
