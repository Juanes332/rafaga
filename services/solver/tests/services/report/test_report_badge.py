"""The wind badge scales with the map, in single and side-by-side report figures."""

import numpy as np
import pytest
from matplotlib.transforms import Bbox

from app.services.render.map_figure import new_map
from app.services.report.report_badge import MAX_BADGE_FRACTION, add_report_wind_badge
from app.services.report.report_comparison import _side_by_side_figure


def _badge_fraction(fig, ax) -> float:
    """Return the longest side of the circle + label union over the axes' shorter side."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    circle = next(p for p in ax.patches if p.get_gid() == "wind_badge").get_window_extent(renderer)
    label = next(t for t in ax.texts if t.get_gid() == "wind_badge_label").get_window_extent(renderer)
    box = Bbox.union([circle, label])
    axes = ax.get_window_extent()
    return max(box.width, box.height) / min(axes.width, axes.height)


@pytest.mark.parametrize("extent", [(0, 100, 0, 100), (0, 300, 0, 60), (0, 60, 0, 300)])
def test_single_map_badge_stays_within_the_cap(extent) -> None:
    fig, ax = new_map(extent, width_in=6.2)
    add_report_wind_badge(ax, 292.5)
    fraction = _badge_fraction(fig, ax)
    assert 0.05 < fraction <= MAX_BADGE_FRACTION * 1.005


def test_side_by_side_badge_matches_the_cap_on_every_panel() -> None:
    k = np.full((20, 40), 1.0)
    panels = [("Caso base", k, None), ("Alt", k * 1.1, None)]
    fig = _side_by_side_figure(panels, (0.0, 200.0, 0.0, 100.0), 270.0)
    fig.canvas.draw()
    axes = [a for a in fig.axes if any(p.get_gid() == "wind_badge" for p in a.patches)]
    assert len(axes) == 2
    for ax in axes:
        assert 0.05 < _badge_fraction(fig, ax) <= MAX_BADGE_FRACTION * 1.005


def test_badge_names_the_wind_direction() -> None:
    fig, ax = new_map((0, 100, 0, 100))
    arrow, label = add_report_wind_badge(ax, 292.5)
    assert label.get_text() == "Desde 292,5°\nU10 10,0 m/s"


def test_badge_label_carries_the_given_u10() -> None:
    fig, ax = new_map((0, 100, 0, 100))
    _, label = add_report_wind_badge(ax, 90.0, u10_ms=7.5)
    assert label.get_text().endswith("U10 7,5 m/s")
