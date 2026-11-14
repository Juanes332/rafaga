"""Colormaps, number formatting and Spanish labels shared by every map."""

import cmocean
import matplotlib

matplotlib.use("Agg")
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

SOLID_COLOR = "#8c8c8c"
K_CMAP = cmocean.cm.speed
SPEED_CMAP = cmocean.cm.speed
DELTA_CMAP = cmocean.cm.balance
ZONE_COLORS = {"neutral": "#f2f2ee", "acceleration": "#d9534f", "stagnation": "#4a78b5",
               "reduction": "#2e8b57"}
LAWSON_COLORS = ["#1a9850", "#91cf60", "#fee08b", "#fc8d59", "#d73027"]
LAWSON_CMAP = ListedColormap(LAWSON_COLORS)
LAWSON_LABELS = {
    "A": "A · Sentarse", "B": "B · Estar de pie", "C": "C · Pasear",
    "D": "D · Caminar con prisa", "E": "E · Incómodo",
}
AXIS_EAST = "Este (m)"
AXIS_NORTH = "Norte (m)"
AXIS_S = "Distancia a lo largo del corte (m)"
AXIS_Z = "Altura (m)"


def decimal_comma(value: float, digits: int = 2) -> str:
    """Return value formatted with a decimal comma (es-CO)."""
    return f"{value:.{digits}f}".replace(".", ",")


def comma_formatter(digits: int = 1) -> FuncFormatter:
    """Return a tick formatter printing decimal commas."""
    return FuncFormatter(lambda v, _pos: decimal_comma(v, digits))


def flat_cmap(color: str) -> ListedColormap:
    """Return a one-colour colormap."""
    return ListedColormap([color])
