"""Compass rose for the report plan maps (maps are north-up)."""

import math

from matplotlib.patches import Polygon

MAX_COMPASS_FRACTION = 0.12  # of the map's shorter side, like the wind badge
_CENTRE = (0.88, 0.86)  # upper-right; the wind badge sits upper-left
_HALF = MAX_COMPASS_FRACTION / 2
_POINTS = (("N", 0.0), ("E", 90.0), ("S", 180.0), ("O", 270.0))


def add_report_compass(ax) -> None:
    """Draw a north-up compass rose with N, E, S, O labels in the upper-right corner."""
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    ratio = abs(y1 - y0) / max(abs(x1 - x0), 1e-9)
    fx, fy = min(1.0, ratio), min(1.0, 1.0 / max(ratio, 1e-9))  # axes fraction per unit of shorter side

    def at(radius: float, bearing: float) -> tuple[float, float]:
        t = math.radians(bearing)
        return (_CENTRE[0] + radius * math.sin(t) * fx, _CENTRE[1] + radius * math.cos(t) * fy)

    def add(points, **style) -> Polygon:
        patch = Polygon(points, closed=True, transform=ax.transAxes, zorder=8, gid="compass", **style)
        ax.add_patch(patch)
        return patch

    ring = [at(_HALF, b) for b in range(0, 360, 10)]
    add(ring, fc="white", ec="#555", lw=0.6, alpha=0.85)
    needle, wide = 0.30 * _HALF, 0.78 * _HALF
    for bearing in (90.0, 180.0, 270.0):
        add([at(needle, bearing - 45), at(wide, bearing), at(needle, bearing + 45), _CENTRE],
            fc="#888", ec="#555", lw=0.4)
    add([at(needle, -45), at(wide, 0.0), at(needle, 45), _CENTRE], fc="#c0392b", ec="#7b241c", lw=0.4)
    for name, bearing in _POINTS:
        x, y = at(0.93 * _HALF, bearing)
        ax.text(x, y, name, transform=ax.transAxes, ha="center", va="center", fontsize=6,
                fontweight="bold", color="#1d1d1b", zorder=9, gid="compass_label",
                bbox={"boxstyle": "circle,pad=0.08", "fc": "white", "ec": "none", "alpha": 0.9})
