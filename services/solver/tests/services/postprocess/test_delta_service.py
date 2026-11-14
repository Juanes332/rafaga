"""Delta K preview against the baseline (US-13): balance map, symmetric limits."""

import json
from pathlib import Path

import numpy as np
import pytest

from app.services.postprocess.delta_service import delta_limit, render_delta


def test_delta_limit_is_symmetric_rounded_and_never_tiny() -> None:
    assert delta_limit(np.array([-0.43, 0.12, np.nan])) == pytest.approx(0.5)
    assert delta_limit(np.array([0.01, -0.02])) == pytest.approx(0.2)
    assert delta_limit(np.full(3, np.nan)) == pytest.approx(0.2)


def test_render_delta_writes_png_and_registers_it_once(result_store) -> None:
    root = result_store.settings.data_dir
    target, base = result_store.dirs[180.0], result_store.dirs[270.0]
    for _ in range(2):
        images = render_delta(root, target, base, None, 180.0, {"dk_reduction": -0.1}, dpi=60)
    manifest = json.loads((Path(root) / target / "manifest.json").read_text())
    assert [i["name"] for i in manifest["images"]].count("delta") == 1
    assert images == manifest["images"]
    assert (Path(root) / target / "images/delta.png").stat().st_size > 5_000
