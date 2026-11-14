"""Export PNG job (SOL-13)."""

import copy
from pathlib import Path

import pytest
from PIL import Image

from app.services.render.render_service import run_render
from tests.support.contracts import example


def _payload(store, layer: str, comfort_dir=None, dpi=300) -> dict:
    raw = copy.deepcopy(example("job.render.example"))
    raw.update({"layer": layer, "result_dir": store.dirs[270.0], "compare_result_dir": store.dirs[180.0],
                "comfort_dir": comfort_dir, "output_grid": store.output_grid, "dpi": dpi})
    return raw


@pytest.mark.parametrize("layer", ["k", "zones", "speed", "delta_k", "lawson"])
def test_every_layer_renders_at_requested_dpi(result_store, comfort_dir, layer) -> None:
    rel = run_render(_payload(result_store, layer, comfort_dir, dpi=320), result_store.settings)
    png = Image.open(Path(result_store.settings.data_dir) / rel)
    assert png.info["dpi"] == pytest.approx((320, 320), abs=0.5)
    assert rel.endswith(".png")


def test_dpi_below_300_is_invalid(result_store) -> None:
    from app.core.errors.solver_errors import InvalidPayloadError

    with pytest.raises(InvalidPayloadError):
        run_render(_payload(result_store, "k", dpi=150), result_store.settings)
