"""Compass rose, cardinal wind text and site coordinates in the PDF report."""

import pytest

from app.services.render.cardinal import cardinal_name, format_dms, wind_from_text
from app.services.render.map_figure import new_map
from app.services.report.report_compass import MAX_COMPASS_FRACTION, add_report_compass
from app.services.report.report_html import project_section


@pytest.mark.parametrize("deg, name", [(0, "N"), (45, "NE"), (90, "E"), (180, "S"), (270, "O"),
                                        (292.5, "ONO"), (337.5, "NNO"), (359.9, "N"), (-90, "O"),
                                        (22.5, "NNE"), (225, "SO")])
def test_cardinal_name_uses_spanish_sixteen_point_rose(deg, name) -> None:
    assert cardinal_name(deg) == name


def test_wind_text_gives_cardinal_and_degrees() -> None:
    assert wind_from_text(45) == "desde NE · 45°"
    assert wind_from_text(292.5) == "desde ONO · 292,5°"


def test_dms_uses_hemispheres_with_oeste_as_o() -> None:
    text = format_dms(4.60976, -74.08175)
    assert text == "4°36′35″ N · 74°04′54″ O"
    assert format_dms(-33.5, 151.25) == "33°30′00″ S · 151°15′00″ E"


def _compass(ax):
    return [p for p in ax.patches if p.get_gid() == "compass"]


@pytest.mark.parametrize("extent", [(0, 100, 0, 100), (0, 300, 0, 60), (0, 60, 0, 300)])
def test_compass_is_capped_and_labels_all_four_points(extent) -> None:
    fig, ax = new_map(extent, width_in=6.2)
    add_report_compass(ax)
    fig.canvas.draw()
    assert _compass(ax)
    labels = {t.get_text() for t in ax.texts if t.get_gid() == "compass_label"}
    assert labels == {"N", "E", "S", "O"}
    axes = ax.get_window_extent()
    box = _compass(ax)[0].get_window_extent()
    assert max(box.width, box.height) / min(axes.width, axes.height) <= MAX_COMPASS_FRACTION + 1e-6


def test_compass_does_not_overlap_the_wind_badge_corner() -> None:
    fig, ax = new_map((0, 100, 0, 100))
    add_report_compass(ax)
    fig.canvas.draw()
    box = _compass(ax)[0].get_window_extent().transformed(ax.transAxes.inverted())
    assert box.x0 > 0.5 and box.y0 > 0.5  # upper-right; the badge lives upper-left


def test_project_section_shows_decimal_and_dms_coordinates() -> None:
    html = project_section({"project": {"lat": 4.60976, "lon": -74.08175}})
    assert "4,60976° N" in html and "74,08175° O" in html
    assert "4°36′35″ N" in html and "74°04′54″ O" in html


def test_every_report_map_carries_the_compass(result_store, comfort_dir, monkeypatch) -> None:
    """Single K, Lawson, side-by-side and dK figures all call the compass."""
    import numpy as np

    from app.services.report import report_charts, report_comparison

    seen = []
    for mod in (report_charts, report_comparison):
        real = mod.add_report_compass
        monkeypatch.setattr(mod, "add_report_compass", lambda ax, real=real: (seen.append(ax), real(ax)))
    k = np.full((20, 40), 1.0)
    report_charts.k_map(k, (0, 200, 0, 100), "t", None, 45.0)
    report_charts.lawson_map(np.zeros((20, 40)), (0, 200, 0, 100), "t")
    fig = report_comparison._side_by_side_figure([("a", k, None), ("b", k, None)], (0, 200, 0, 100), 45.0)
    assert len(seen) == 4
    assert sum(1 for a in fig.axes if any(t.get_gid() == "compass_label" for t in a.texts)) == 2


@pytest.mark.parametrize(("deg", "name"), [(348.75, "N"), (348.74, "NNO"), (11.25, "NNE"), (11.24, "N")])
def test_cardinal_name_splits_on_sector_boundaries(deg, name) -> None:
    assert cardinal_name(deg) == name


def test_wind_text_wraps_degrees_into_zero_to_360() -> None:
    assert wind_from_text(359.96) == "desde N · 0°"
    assert wind_from_text(-45) == "desde NO · 315°"


def test_coordinates_that_round_to_zero_take_north_and_east() -> None:
    from app.services.render.cardinal import format_decimal

    assert format_dms(-1e-7, -1e-7) == "0°00′00″ N · 0°00′00″ E"
    assert format_decimal(-1e-7, -1e-7) == "0,00000° N · 0,00000° E"


def test_dms_carries_59_9999_seconds_into_the_minute() -> None:
    assert format_dms(5 + 32 / 60 + 59.9999 / 3600, 0).startswith("5°33′00″ N")
