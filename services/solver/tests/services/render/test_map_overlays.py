"""Facade elements, wind arrow and smooth display on every plan map (US-11/14)."""

import numpy as np
from matplotlib.collections import PathCollection
from matplotlib.patches import Polygon

from app.models.scene.scene_schemas import Scene
from app.services.render.map_decorations import add_facade_elements, add_wind_arrow
from app.services.render.map_figure import fill_solids, new_map
from tests.support.scenario_factory import SceneBuilder


def _scene() -> Scene:
    b = SceneBuilder().block("A", 0, 0, 30, 12, 18)
    b.canopy("canopy-1", 0, -3, 30, 0, 4.0)
    b.screen("screen-1", 0, -2.1, 30, -2.0, 18, (0.0, -1.0))
    b.fin("fins-1", -0.5, 5.9, 0.0, 6.1, 18)
    b.vegetation("veg-1", 32, 0, 36, 12, 5)
    return Scene.model_validate(b.build())


def test_each_element_kind_gets_its_own_symbol() -> None:
    fig, ax = new_map((-20, 50, -20, 30))
    drawn = add_facade_elements(ax, _scene())
    assert drawn == {"building": 1, "canopy": 1, "screen": 1, "fin": 1, "vegetation": 1}
    patches = {p.get_gid(): p for p in ax.patches if isinstance(p, Polygon)}
    assert patches["canopy"].get_hatch() and not patches["canopy"].get_fill()
    assert any(line.get_gid() == "screen" and line.get_linestyle() == "--" for line in ax.lines)
    assert any(isinstance(c, PathCollection) and c.get_gid() == "vegetation" for c in ax.collections)


def test_wind_arrow_points_downwind_and_names_the_direction() -> None:
    fig, ax = new_map((0, 100, 0, 100))
    arrow, label = add_wind_arrow(ax, 292.5)
    assert label.get_text() == "Viento desde 292,5°"
    (x0, y0), (x1, y1) = arrow.xyann, arrow.xy
    assert x1 > x0 and y1 < y0  # from WNW the flow heads ESE


def test_fill_solids_copies_the_nearest_fluid_value() -> None:
    k = np.array([[1.0, np.nan, 3.0], [1.0, 2.0, 3.0]])
    out = fill_solids(k)
    assert np.isfinite(out).all() and out[0, 1] in (1.0, 2.0, 3.0)
