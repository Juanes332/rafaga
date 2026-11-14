"""Scale bar, north arrow, outlines and footer text for export maps (SOL-13)."""

import math

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Patch
from matplotlib.patches import Polygon as PolygonPatch
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar

from app.models.scene.scene_schemas import Scene
from app.services.render.map_style import SOLID_COLOR, decimal_comma

ELEMENT_COLOR = "#1d1d1b"
VEGETATION_COLOR = "#2f7d32"


def nice_length(span_m: float) -> float:
    """Return a round scale-bar length near a fifth of the span."""
    target = span_m / 5.0
    power = 10 ** math.floor(math.log10(max(target, 1e-9)))
    for step in (1, 2, 5, 10):
        if step * power >= target:
            return step * power
    return 10 * power


def add_scale_bar(ax, extent) -> None:
    """Draw a metric scale bar in the lower-left corner."""
    length = nice_length(extent[1] - extent[0])
    label = f"{length:g} m".replace(".", ",")
    bar = AnchoredSizeBar(ax.transData, length, label, "lower left", pad=0.5, sep=4,
                          frameon=True, size_vertical=(extent[3] - extent[2]) / 150)
    ax.add_artist(bar)


def add_north_arrow(ax) -> None:
    """Draw a north arrow (output grids are north-up)."""
    ax.annotate("N", xy=(0.95, 0.95), xytext=(0.95, 0.83), xycoords="axes fraction",
                ha="center", va="center", fontsize=11, fontweight="bold",
                arrowprops={"facecolor": "black", "width": 4, "headwidth": 11})


def add_outlines(ax, scene: Scene | None) -> None:
    """Outline every solid footprint of the scene."""
    if scene is None:
        return
    for solid in scene.solids:
        ax.add_patch(PolygonPatch(solid.footprint, closed=True, fill=False, lw=0.6, ec="#222"))


def add_footer(fig, wind_text: str, disclaimer: str) -> None:
    """Write the reference wind and the disclaimer under the map."""
    fig.text(0.01, 0.035, wind_text, fontsize=8, ha="left")
    fig.text(0.01, 0.01, disclaimer, fontsize=7, ha="left", style="italic")


def _long_axis(footprint) -> tuple[np.ndarray, np.ndarray]:
    """Return the end points of a thin rectangle's centre line."""
    pts = np.asarray(footprint, dtype=float)
    centre = pts.mean(axis=0)
    _, _, vt = np.linalg.svd(pts - centre)
    proj = (pts - centre) @ vt[0]
    return centre + proj.min() * vt[0], centre + proj.max() * vt[0]


def _draw_screen(ax, item) -> None:
    """Draw a porous screen as a dashed line along its length."""
    a, b = _long_axis(item.footprint)
    ax.add_line(Line2D([a[0], b[0]], [a[1], b[1]], ls="--", lw=1.6, color=ELEMENT_COLOR,
                       gid="screen", zorder=6))


def _draw_vegetation(ax, item) -> None:
    """Draw a vegetation volume as a dotted outline with tree symbols."""
    ax.add_patch(PolygonPatch(item.footprint, closed=True, fill=False, ls=":", lw=0.8,
                              ec=VEGETATION_COLOR, gid="vegetation_area", zorder=6))
    pts = np.asarray(item.footprint, dtype=float)
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    n = max(1, int(max(hi - lo) // 4))
    t = (np.arange(n) + 0.5) / n
    xs = lo[0] + t * (hi[0] - lo[0]) if hi[0] - lo[0] >= hi[1] - lo[1] else np.full(n, (lo[0] + hi[0]) / 2)
    ys = lo[1] + t * (hi[1] - lo[1]) if hi[0] - lo[0] < hi[1] - lo[1] else np.full(n, (lo[1] + hi[1]) / 2)
    ax.scatter(xs, ys, s=28, marker="o", facecolors="none", edgecolors=VEGETATION_COLOR,
               linewidths=1.1, gid="vegetation", zorder=7)


def add_facade_elements(ax, scene: Scene | None) -> dict[str, int]:
    """Draw buildings (grey), canopies (hatched), fins (dark), screens (dashed), vegetation.

    Return how many primitives of each kind were drawn.
    """
    drawn: dict[str, int] = {}
    if scene is None:
        return drawn
    for solid in scene.solids:
        kind = solid.origin.kind
        if kind == "canopy":
            patch = PolygonPatch(solid.footprint, closed=True, fill=False, hatch="////", lw=0.8,
                                 ec=ELEMENT_COLOR, gid="canopy", zorder=6)
        elif kind == "fin":
            patch = PolygonPatch(solid.footprint, closed=True, fc=ELEMENT_COLOR, ec=ELEMENT_COLOR,
                                 lw=1.2, gid="fin", zorder=6)
        else:
            kind = "building"
            patch = PolygonPatch(solid.footprint, closed=True, fc=SOLID_COLOR, ec="#222", lw=0.6,
                                 gid="building", zorder=5)
        ax.add_patch(patch)
        drawn[kind] = drawn.get(kind, 0) + 1
    for item in scene.porous:
        kind = "screen" if item.model == "screen" else "vegetation"
        (_draw_screen if kind == "screen" else _draw_vegetation)(ax, item)
        drawn[kind] = drawn.get(kind, 0) + 1
    return drawn


def element_legend_handles(drawn: dict[str, int]) -> list:
    """Return legend handles for the facade element kinds present."""
    handles = []
    if drawn.get("screen"):
        handles.append(Line2D([], [], ls="--", lw=1.6, color=ELEMENT_COLOR, label="Celosía"))
    if drawn.get("canopy"):
        handles.append(Patch(fill=False, hatch="////", ec=ELEMENT_COLOR, label="Marquesina"))
    if drawn.get("fin"):
        handles.append(Patch(fc=ELEMENT_COLOR, label="Aletas"))
    if drawn.get("vegetation"):
        handles.append(Line2D([], [], ls="", marker="o", mfc="none", mec=VEGETATION_COLOR,
                              label="Vegetación"))
    return handles


def add_wind_arrow(ax, wind_from_deg: float):
    """Draw the flow direction in the upper-left corner; return (arrow, label)."""
    phi = math.radians(wind_from_deg)
    d = (-math.sin(phi), -math.cos(phi))
    cx, cy, half = 0.1, 0.87, 0.06
    tail = (cx - half * d[0], cy - half * d[1])
    head = (cx + half * d[0], cy + half * d[1])
    ax.add_patch(Circle((cx, cy), 0.085, transform=ax.transAxes, fc="white", ec="#555",
                        lw=0.6, alpha=0.85, zorder=8))
    arrow = ax.annotate("", xy=head, xytext=tail, xycoords="axes fraction",
                        textcoords="axes fraction", zorder=9,
                        arrowprops={"arrowstyle": "-|>,head_width=0.35,head_length=0.6",
                                    "lw": 2.2, "color": "#c0392b", "shrinkA": 0, "shrinkB": 0})
    label = ax.annotate(f"Viento desde {decimal_comma(wind_from_deg, 1)}°", xy=(cx, cy - 0.1),
                        xycoords="axes fraction", fontsize=7.5, ha="center", va="top", zorder=9,
                        bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "#555",
                              "lw": 0.6, "alpha": 0.85})
    return arrow, label
