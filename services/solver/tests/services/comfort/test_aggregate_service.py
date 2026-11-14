"""Aggregate job on real results (SOL-12)."""

import json
from pathlib import Path

import numpy as np
import pytest

from app.services.comfort.aggregate_service import run_aggregate
from tests.support.result_store import aggregate_payload


def test_aggregate_writes_classes_exceedance_and_row(result_store) -> None:
    row = run_aggregate(aggregate_payload(result_store), result_store.settings)
    folder = Path(result_store.settings.data_dir) / row["dir"]
    shape = [result_store.output_grid["ny"], result_store.output_grid["nx"]]
    classes = np.fromfile(folder / "fields/lawson_class.u8", dtype=np.uint8).reshape(shape)
    assert set(np.unique(classes)) <= {0, 1, 2, 3, 4, 255}
    exc = np.fromfile(folder / "fields/exceedance.f32", dtype="<f4").reshape([6] + shape)
    assert np.nanmax(exc) <= 1.0
    assert row["coverage"] == pytest.approx((0.09 + 0.05) / 0.96, abs=1e-6)
    assert row["partial"] is True
    assert sum(c["percent"] for c in row["class_areas"]) == pytest.approx(100.0, abs=0.01)
    assert (folder / "images/lawson.png").exists()
    assert json.loads((folder / "manifest.json").read_text())["lawson_hash"] == row["lawson_hash"]


def test_result_on_another_grid_is_an_invalid_payload(result_store) -> None:
    from app.core.errors.solver_errors import InvalidPayloadError

    raw = aggregate_payload(result_store)
    raw["output_grid"] = dict(raw["output_grid"], nx=raw["output_grid"]["nx"] + 1)
    with pytest.raises(InvalidPayloadError) as err:
        run_aggregate(raw, result_store.settings)
    assert err.value.details["reason"] == "grid_mismatch"
