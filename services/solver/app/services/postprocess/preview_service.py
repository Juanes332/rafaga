"""150 dpi previews k.png, speed.png, zones.png (+ 3D slices) (SOL-11, US-11)."""

from pathlib import Path

from app.models.jobs.payload_schemas import HeavyPayload
from app.services.postprocess.output_fields import OutputFields
from app.services.render import map_style as st
from app.services.report.report_badge import add_report_wind_badge
from app.services.render.map_decorations import (
    add_facade_elements,
    element_legend_handles,
)
from app.services.render.map_figure import (
    draw_scalar,
    draw_zones,
    new_map,
    save_png,
    zone_categories,
)


def _labels(section: bool) -> tuple[str, str]:
    """Return axis labels for plan or section maps."""
    return (st.AXIS_S, st.AXIS_Z) if section else (st.AXIS_EAST, st.AXIS_NORTH)


def decorate_plan(fig, ax, payload: HeavyPayload, legend: bool = True) -> None:
    """Draw facade elements, the wind arrow and an element legend on a plan map."""
    drawn = add_facade_elements(ax, payload.scene)
    add_report_wind_badge(ax, payload.wind.wind_from_deg)
    handles = element_legend_handles(drawn)
    if legend and handles:
        fig.legend(handles=handles, loc="outside lower center", ncols=len(handles), fontsize=7,
                   frameon=False)


def write_previews(fields: OutputFields, payload: HeavyPayload, out_dir: Path,
                   section: bool) -> list[dict]:
    """Render the three previews and return manifest image entries."""
    images = out_dir / "images"
    images.mkdir(parents=True, exist_ok=True)
    hint = payload.render
    k, extent, labels = fields.arrays["K"], fields.extent, _labels(section)
    smooth = not section
    fig, ax = new_map(extent, labels=labels)
    draw_scalar(fig, ax, k, extent, st.K_CMAP, "K = U / U_ref(z_a) (adimensional)", vmin=0.0,
                smooth=smooth)
    ax.set_title("Coeficiente de velocidad K")
    if smooth:
        decorate_plan(fig, ax, payload)
    save_png(fig, images / "k.png", hint.dpi)
    fig, ax = new_map(extent, labels=labels)
    draw_scalar(fig, ax, fields.arrays["speed"], extent, st.SPEED_CMAP,
                "Velocidad media (m/s)", vmin=0.0, digits=1, smooth=smooth)
    ax.set_title("Velocidad media del viento")
    if smooth:
        decorate_plan(fig, ax, payload)
    save_png(fig, images / "speed.png", hint.dpi)
    fig, ax = new_map(extent, labels=labels)
    draw_zones(ax, zone_categories(k, hint.k_accel, hint.k_stagnation), extent,
               hint.k_accel, hint.k_stagnation)
    ax.set_title("Zonas de aceleración y estancamiento")
    if smooth:
        decorate_plan(fig, ax, payload)
    save_png(fig, images / "zones.png", hint.dpi)
    return [{"name": n, "file": f"images/{n}.png"} for n in ("k", "speed", "zones")]
