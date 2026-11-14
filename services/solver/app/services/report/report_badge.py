"""Wind-direction badge sized relative to the map, for report figures.

The circle and its label (direction and U10) form one block whose longest
side stays within MAX_BADGE_FRACTION of the axes' shorter side.
"""

import math

from matplotlib.patches import Circle
from matplotlib.text import Text
from matplotlib.transforms import Transform

from app.services.render.map_style import decimal_comma

MAX_BADGE_FRACTION = 0.12  # circle + label union over the axes' shorter side
NOMINAL_U10_MS = 10.0  # reference wind of every normalised (K) run
_HALF = MAX_BADGE_FRACTION / 2
_RADIUS = 0.034
_CIRCLE_Y = _HALF - _RADIUS  # circle touches the top of the block
_LABEL_TOP = _CIRCLE_Y - _RADIUS - 0.002
_LABEL_WIDTH = MAX_BADGE_FRACTION * 0.92  # slack: hinting varies with the save dpi
_LABEL_HEIGHT = _LABEL_TOP + _HALF - 0.008  # slack for pixel rounding on small maps
_PAD = 0.2  # boxstyle pad, in font sizes
_MAX_FONT_PT = 6.5
_MIN_FONT_PT = 0.5
_CENTRE = (0.14, 0.86)  # axes fraction, upper-left corner


class _ShorterSideUnits(Transform):
    """Map (u, v) to pixels: origin at a fixed axes point, 1 unit = shorter axes side."""

    input_dims = output_dims = 2

    def __init__(self, ax, centre: tuple[float, float]) -> None:
        """Bind the transform to the axes so layout changes invalidate it."""
        super().__init__()
        self._ax, self._centre = ax, centre
        self.set_children(ax.transAxes)

    def transform_non_affine(self, values):
        """Scale by the axes' current shorter side and shift to the centre."""
        box = self._ax.bbox
        origin = self._ax.transAxes.transform(self._centre)
        return origin + values * min(box.width, box.height)

    def inverted(self):
        """Return the inverse (needed by matplotlib's artist machinery)."""
        raise NotImplementedError("badge transform is draw-only")


class _FittedLabel(Text):
    """Text whose font size is refit on every draw to the badge's slot."""

    def __init__(self, ax, text: str, units: Transform) -> None:
        """Place the label under the circle, in badge units."""
        super().__init__(0.0, _LABEL_TOP, text, transform=units, ha="center", va="top",
                         zorder=9, gid="wind_badge_label",
                         bbox={"boxstyle": f"round,pad={_PAD}", "fc": "white", "ec": "#555",
                               "lw": 0.6, "alpha": 0.85})
        self._ax = ax

    def _fit(self, renderer) -> None:
        """Pick the largest font whose padded box fits the slot at this size."""
        short = min(self._ax.bbox.width, self._ax.bbox.height)
        size = _MAX_FONT_PT
        # Glyph extents are not linear in size at small sizes (hinting), so
        # shrink until the measured box fits instead of trusting a ratio.
        for _ in range(80):
            self.set_fontsize(size)
            box = Text.get_window_extent(self, renderer)
            pad = 2 * _PAD * renderer.points_to_pixels(size)
            scale = min(_LABEL_WIDTH * short / (box.width + pad),
                        _LABEL_HEIGHT * short / (box.height + pad))
            if scale >= 1.0 or size <= _MIN_FONT_PT:
                break
            size = max(_MIN_FONT_PT, size * min(scale, 0.98))
        self.set_fontsize(size)
        top = _LABEL_TOP - _PAD * renderer.points_to_pixels(size) / short
        self.set_position((0.0, top))

    def draw(self, renderer) -> None:
        """Refit then draw."""
        self._fit(renderer)
        super().draw(renderer)

    def get_window_extent(self, renderer=None, dpi=None):
        """Return the extent at the fitted size."""
        renderer = renderer or self.get_figure(root=True)._get_renderer()
        self._fit(renderer)
        return super().get_window_extent(renderer, dpi)


def add_report_wind_badge(ax, wind_from_deg: float, u10_ms: float = NOMINAL_U10_MS):
    """Draw the flow direction badge capped at 12 % of the map; return (arrow, label)."""
    phi = math.radians(wind_from_deg)
    d = (-math.sin(phi), -math.cos(phi))
    units = _ShorterSideUnits(ax, _CENTRE)
    half = _RADIUS * 0.62
    ax.add_patch(Circle((0, _CIRCLE_Y), _RADIUS, transform=units, fc="white", ec="#555", lw=0.6,
                        alpha=0.85, zorder=8, gid="wind_badge"))
    arrow = ax.annotate("", xy=(half * d[0], _CIRCLE_Y + half * d[1]),
                        xytext=(-half * d[0], _CIRCLE_Y - half * d[1]),
                        xycoords=units, textcoords=units, zorder=9,
                        arrowprops={"arrowstyle": "-|>,head_width=0.3,head_length=0.5",
                                    "lw": 1.6, "color": "#c0392b", "shrinkA": 0, "shrinkB": 0})
    text = f"Desde {decimal_comma(wind_from_deg, 1)}°\nU10 {decimal_comma(u10_ms, 1)} m/s"
    label = _FittedLabel(ax, text, units)
    ax.add_artist(label)
    return arrow, label
