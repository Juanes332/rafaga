"""Charts embedded in the PDF report: wind rose and result maps."""

import base64
import io

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from app.services.render import map_style as st
from app.services.render.map_decorations import (
    add_facade_elements,
    element_legend_handles,
)
from app.services.render.map_figure import draw_lawson, draw_scalar, new_map
from app.services.report.report_badge import add_report_wind_badge
from app.services.report.report_compass import add_report_compass


def png_data_uri(fig, dpi: int = 150) -> str:
    """Return a figure as a base64 PNG data URI."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def rose_chart(rose: dict) -> str | None:
    """Return the 16-sector frequency rose (meteorological 'from')."""
    sectors = rose.get("sectors") or []
    if not sectors:
        return None
    fig = Figure(figsize=(4.2, 4.2), layout="constrained")
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(projection="polar")
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    theta = np.radians([s["center_deg"] for s in sectors])
    freq = [100.0 * s.get("frequency", 0.0) for s in sectors]
    ax.bar(theta, freq, width=np.radians(360 / len(sectors)) * 0.9, color="#3c6e8f", edgecolor="white")
    ax.set_title("Frecuencia por sector (%)", fontsize=9)
    ax.yaxis.set_major_formatter(st.comma_formatter(0))
    return png_data_uri(fig)


def k_map(k: np.ndarray, extent, title: str, scene=None, wind_from_deg: float | None = None) -> str:
    """Return a K map (with facade elements and wind arrow when known) as data URI."""
    fig, ax = new_map(extent, width_in=6.2)
    draw_scalar(fig, ax, k, extent, st.K_CMAP, "K (adimensional)", vmin=0.0, smooth=scene is not None)
    handles = element_legend_handles(add_facade_elements(ax, scene))
    if wind_from_deg is not None:
        add_report_wind_badge(ax, wind_from_deg)
    add_report_compass(ax)
    if handles:
        fig.legend(handles=handles, loc="outside lower center", ncols=len(handles), fontsize=7,
                   frameon=False)
    ax.set_title(title, fontsize=9)
    return png_data_uri(fig, dpi=130)


def lawson_map(classes: np.ndarray, extent, title: str) -> str:
    """Return a Lawson class map as data URI."""
    fig, ax = new_map(extent, width_in=6.2)
    draw_lawson(fig, ax, classes, extent)
    add_report_compass(ax)
    ax.set_title(title, fontsize=9)
    return png_data_uri(fig, dpi=130)
