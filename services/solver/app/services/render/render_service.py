"""Export PNG job: one layer at >= 300 dpi with full map furniture (SOL-13)."""

import json

import numpy as np

from app.configs.config import Settings
from app.models.jobs.payload_parser import parse_payload
from app.models.jobs.payload_schemas import RenderPayload
from app.services.render import map_style as st
from app.services.render.map_decorations import (
    add_footer, add_north_arrow, add_outlines, add_scale_bar,
)
from app.services.render.map_figure import (
    draw_lawson, draw_scalar, draw_zones, new_map, save_png, zone_categories,
)
from app.services.storage import output_dir_service as storage

DEFAULT_DISCLAIMER = (
    "Herramienta de anteproyecto: compara alternativas, no sustituye un ensayo en túnel de viento."
)


def load_field(root: str, rel_dir: str, name: str) -> np.ndarray:
    """Return a field of a result/comfort directory by logical name."""
    folder = storage.resolve(root, rel_dir)
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    entry = next(e for e in manifest["fields"] if e["name"] == name)
    dtype = "<f4" if entry["dtype"] == "float32" else np.uint8
    return np.fromfile(folder / entry["file"], dtype=dtype).reshape(entry["shape"])


def _draw_layer(fig, ax, p: RenderPayload, root: str, extent) -> str:
    """Draw the requested layer and return its title."""
    th = {"k_accel": 1.2, "k_stagnation": 0.3, "dk_reduction": -0.1} | p.thresholds
    if p.layer == "lawson":
        draw_lawson(fig, ax, load_field(root, p.comfort_dir, "lawson_class"), extent)
        return "Confort peatonal (Lawson LDDC)"
    k = load_field(root, p.result_dir, "K")
    if p.layer == "k":
        draw_scalar(fig, ax, k, extent, st.K_CMAP, "K = U / U_ref(z_a) (adimensional)", vmin=0.0)
        return "Coeficiente de velocidad K"
    if p.layer == "speed":
        speed = load_field(root, p.result_dir, "speed")
        draw_scalar(fig, ax, speed, extent, st.SPEED_CMAP, "Velocidad media (m/s)", vmin=0.0, digits=1)
        return "Velocidad media del viento"
    delta = None
    if p.compare_result_dir:
        delta = load_field(root, p.compare_result_dir, "K") - k
    if p.layer == "delta_k":
        lim = float(np.nanmax(np.abs(delta))) if delta is not None and np.isfinite(delta).any() else 1.0
        draw_scalar(fig, ax, delta, extent, st.DELTA_CMAP, "ΔK = K_B − K_A (adimensional)", -lim, lim)
        return "Diferencia de K entre alternativas"
    cat = zone_categories(k, th["k_accel"], th["k_stagnation"], delta, th["dk_reduction"] if delta is not None else None)
    draw_zones(ax, cat, extent, th["k_accel"], th["k_stagnation"],
               th["dk_reduction"] if delta is not None else None)
    return "Zonas de aceleración y estancamiento"


def run_render(raw: dict, settings: Settings) -> str:
    """Render the export PNG and return its path relative to DATA_DIR."""
    p = parse_payload(RenderPayload, raw)
    g = p.output_grid
    extent = (g.origin_x, g.origin_x + g.nx * g.dx_m, g.origin_y, g.origin_y + g.ny * g.dx_m)
    fig, ax = new_map(extent, width_in=8.0)
    title = _draw_layer(fig, ax, p, settings.data_dir, extent)
    names = " / ".join(v for k, v in p.labels.items() if k.startswith("alternative_") and v)
    ax.set_title(f"{p.labels.get('project_name', '')} · {title}\n{names}".strip(" ·\n"), fontsize=10)
    add_outlines(ax, p.scene)
    add_scale_bar(ax, extent)
    add_north_arrow(ax)
    fig.get_layout_engine().set(rect=(0, 0.06, 1, 0.94))
    add_footer(fig, f"Viento de referencia: {p.labels.get('wind', '')}",
               p.labels.get("disclaimer") or DEFAULT_DISCLAIMER)
    folder = storage.resolve(settings.data_dir, p.output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / f".{p.file_name}.tmp"
    save_png(fig, tmp, p.dpi)
    tmp.replace(folder / p.file_name)
    return f"{p.output_dir.rstrip('/')}/{p.file_name}"
