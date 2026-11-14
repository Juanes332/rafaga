"""Every map figure of a full PNG/report generation keeps its badge within 12 % (BL-07).

Savefig is intercepted, so the figures measured are the ones actually written: previews of a
real heavy job, the delta map, the report K map and the side-by-side figure, on portrait and
landscape maps.
"""

from io import BytesIO

import numpy as np
import pytest
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox

from app.configs.config import Settings
from app.services.postprocess.delta_service import delta_figure
from app.services.report.report_badge import MAX_BADGE_FRACTION
from app.services.report.report_charts import k_map
from app.services.report.report_comparison import _side_by_side
from app.services.simulation.heavy_job_service import run_heavy_job
from tests.support.payload_factory import plan_payload

TOLERANCE = 1.005
LANDSCAPE, PORTRAIT = (0.0, 300.0, 0.0, 80.0), (0.0, 80.0, 0.0, 300.0)


@pytest.fixture
def measurements(monkeypatch):
    """Record (kind, fraction, label) for each badge in every figure saved as PNG."""
    found: list[tuple[float, str]] = []
    original = Figure.savefig

    def spy(self, *args, **kwargs):
        original(self, *args, **kwargs)
        renderer = self.canvas.get_renderer()
        for ax in self.axes:
            circle = next((p for p in ax.patches if p.get_gid() == "wind_badge"), None)
            label = next((t for t in ax.texts if t.get_gid() == "wind_badge_label"), None)
            if circle is None or label is None:
                continue
            box = Bbox.union([circle.get_window_extent(renderer), label.get_window_extent(renderer)])
            axes = ax.get_window_extent(renderer)
            found.append((max(box.width, box.height) / min(axes.width, axes.height), label.get_text()))
        return None

    monkeypatch.setattr(Figure, "savefig", spy)
    return found


def _assert_all_within(found, minimum: int) -> None:
    assert len(found) >= minimum
    for fraction, text in found:
        assert 0.04 < fraction <= MAX_BADGE_FRACTION * TOLERANCE, (fraction, text)
        assert "U10" in text and "Desde" in text


@pytest.mark.parametrize("extent", [LANDSCAPE, PORTRAIT], ids=["landscape", "portrait"])
def test_report_figures_keep_the_badge_within_the_cap(measurements, extent) -> None:
    ny, nx = (20, 75) if extent is LANDSCAPE else (75, 20)
    k = np.linspace(0.5, 1.5, nx * ny).reshape(ny, nx)
    k_map(k, extent, "K", None, 292.5)
    _side_by_side([("Base", k, None), ("Alt", k * 1.1, None)], extent, 292.5)
    fig, _ = delta_figure(k * 0.1 - 0.05, extent, None, 292.5, -0.1)
    fig.savefig(BytesIO(), format="png")
    _assert_all_within(measurements, 4)


@pytest.mark.parametrize("dx", [6.0])
def test_previews_of_a_full_job_keep_the_badge_within_the_cap(measurements, tmp_path, dx) -> None:
    raw = plan_payload(dx=dx, device="cpu")
    run_heavy_job(raw, "j", Settings(data_dir=str(tmp_path)), lambda *_: False)
    _assert_all_within(measurements, 3)  # k, speed and zones previews
