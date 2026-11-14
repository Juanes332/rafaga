"""Build matplotlib map figures (thread-safe OO API, no pyplot)."""

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import Patch
from scipy.ndimage import distance_transform_edt

from app.services.render import map_style as st


def new_map(extent: tuple[float, float, float, float], width_in: float = 7.5,
            labels: tuple[str, str] = (st.AXIS_EAST, st.AXIS_NORTH)):
    """Return (figure, axes) sized to the extent's aspect ratio."""
    x0, x1, y0, y1 = extent
    aspect = (y1 - y0) / max(x1 - x0, 1e-9)
    height = min(max(width_in * aspect * 0.62 + 1.0, 3.0), 11.0)
    fig = Figure(figsize=(width_in, height), layout="constrained")
    FigureCanvasAgg(fig)
    ax = fig.add_subplot()
    ax.set_xlabel(labels[0])
    ax.set_ylabel(labels[1])
    ax.set_aspect("equal")
    ax.xaxis.set_major_formatter(st.comma_formatter(0))
    ax.yaxis.set_major_formatter(st.comma_formatter(0))
    return fig, ax


def fill_solids(field: np.ndarray) -> np.ndarray:
    """Return the field with NaN cells set to the nearest finite value."""
    bad = ~np.isfinite(field)
    if not bad.any() or bad.all():
        return field
    _, (iy, ix) = distance_transform_edt(bad, return_indices=True)
    return field[iy, ix]


def draw_scalar(fig, ax, field, extent, cmap, label: str, vmin=None, vmax=None, digits=2,
                smooth: bool = False, colorbar: bool = True):
    """Draw a scalar field with solids grey and a numeric colorbar.

    `smooth` interpolates bilinearly for display (solid cells take the
    nearest fluid value); the caller then draws the exact building
    polygons on top so the coarse cell mask never shows.
    """
    cmap = cmap.with_extremes(bad=st.SOLID_COLOR)
    data = fill_solids(field) if smooth else np.ma.masked_invalid(field)
    image = ax.imshow(data, origin="lower", extent=extent, cmap=cmap, vmin=vmin, vmax=vmax,
                      interpolation="bilinear" if smooth else "nearest")
    if not colorbar:
        return image
    bar = fig.colorbar(image, ax=ax, shrink=0.85)
    bar.set_label(label)
    bar.ax.yaxis.set_major_formatter(st.comma_formatter(digits))
    return image


def zone_categories(k: np.ndarray, k_accel: float, k_stag: float,
                    delta: np.ndarray | None = None, dk_reduction: float | None = None):
    """Return 0 neutral, 1 acceleration, 2 stagnation, 3 reduction, -1 solid."""
    cat = np.zeros(k.shape, dtype=np.int8)
    cat[k > k_accel] = 1
    cat[k < k_stag] = 2
    if delta is not None and dk_reduction is not None:
        cat[np.nan_to_num(delta, nan=0.0) < dk_reduction] = 3
    cat[~np.isfinite(k)] = -1
    return cat


def draw_zones(ax, cat: np.ndarray, extent, k_accel: float, k_stag: float,
               dk_reduction: float | None = None) -> None:
    """Draw hatched zones distinguishable without colour, plus a legend."""
    colors = st.ZONE_COLORS
    specs = [(1, "acceleration", "///", f"Aceleración (K > {st.decimal_comma(k_accel)})"),
             (2, "stagnation", "...", f"Estancamiento (K < {st.decimal_comma(k_stag)})")]
    if dk_reduction is not None:
        specs.append((3, "reduction", "xx", f"Reducción (ΔK < {st.decimal_comma(dk_reduction)})"))
    base = np.where(cat == -1, np.nan, 0.0)
    ax.imshow(np.ma.masked_invalid(base), origin="lower", extent=extent,
              cmap=_flat(colors["neutral"]), interpolation="nearest")
    ny, nx = cat.shape
    hx, hy = (extent[1] - extent[0]) / nx, (extent[3] - extent[2]) / ny
    xs = extent[0] + (np.arange(nx) + 0.5) * hx
    ys = extent[2] + (np.arange(ny) + 0.5) * hy
    handles = [Patch(facecolor=colors["neutral"], edgecolor="#555", label="Neutra")]
    for value, key, hatch, label in specs:
        ax.contourf(xs, ys, (cat == value).astype(float), levels=[0.5, 1.5],
                    colors=[colors[key]], hatches=[hatch], alpha=0.85)
        handles.append(Patch(facecolor=colors[key], hatch=hatch, edgecolor="#222", label=label))
    handles.append(Patch(facecolor=st.SOLID_COLOR, label="Edificación"))
    _solid_overlay(ax, cat == -1, extent)
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8)


def draw_lawson(fig, ax, classes: np.ndarray, extent) -> None:
    """Draw Lawson classes A..E with a labelled discrete legend."""
    data = np.where(classes == 255, np.nan, classes.astype(float))
    cmap = st.LAWSON_CMAP.copy()
    cmap.set_bad(st.SOLID_COLOR)
    ax.imshow(np.ma.masked_invalid(data), origin="lower", extent=extent, cmap=cmap,
              vmin=-0.5, vmax=4.5, interpolation="nearest")
    handles = [Patch(facecolor=c, label=st.LAWSON_LABELS[k])
               for k, c in zip("ABCDE", st.LAWSON_COLORS)]
    handles.append(Patch(facecolor=st.SOLID_COLOR, label="Edificación"))
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8,
              title="Confort Lawson")


def _flat(color: str):
    """Return a one-colour colormap."""
    from matplotlib.colors import ListedColormap  # noqa: PLC0415

    return ListedColormap([color])


def _solid_overlay(ax, solid: np.ndarray, extent) -> None:
    """Paint solid cells grey on top of everything."""
    layer = np.where(solid, 1.0, np.nan)
    ax.imshow(np.ma.masked_invalid(layer), origin="lower", extent=extent,
              cmap=_flat(st.SOLID_COLOR), interpolation="nearest")


def save_png(fig, path, dpi: int) -> None:
    """Write the figure as PNG; matplotlib stores dpi in the pHYs chunk."""
    fig.savefig(path, dpi=dpi, format="png")
