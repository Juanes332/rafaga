"""delta.png: K of an alternative minus its baseline (US-13, FR-49)."""

import json
import math
from pathlib import Path

import numpy as np

from app.models.scene.scene_schemas import Scene
from app.services.postprocess.field_writer import write_json
from app.services.render import map_style as st
from app.services.report.report_badge import add_report_wind_badge
from app.services.render.map_decorations import (
    add_facade_elements,
    element_legend_handles,
)
from app.services.render.map_figure import draw_scalar, new_map, save_png
from app.services.storage import output_dir_service as storage

_MIN_LIMIT = 0.2


def delta_limit(delta: np.ndarray) -> float:
    """Return the symmetric colour limit: max |dK| rounded up to 0.1, >= 0.2."""
    finite = np.abs(delta[np.isfinite(delta)])
    peak = float(finite.max()) if finite.size else 0.0
    return max(_MIN_LIMIT, math.ceil(round(peak * 10, 6)) / 10)


def _field(folder: Path, name: str) -> np.ndarray:
    """Return a field of a result directory by logical name."""
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    entry = next(e for e in manifest["fields"] if e["name"] == name)
    return np.fromfile(folder / entry["file"], dtype="<f4").reshape(entry["shape"])


def delta_figure(delta: np.ndarray, extent, scene: Scene | None, wind_from_deg: float | None,
                 dk_reduction: float, width_in: float = 7.5, title: str | None = None):
    """Return (fig, ax) of a dK map with reduction zones outlined."""
    fig, ax = new_map(extent, width_in=width_in)
    lim = delta_limit(delta)
    draw_scalar(fig, ax, delta, extent, st.DELTA_CMAP,
                "ΔK = K alternativa − K base (adimensional)", -lim, lim, smooth=scene is not None)
    ny, nx = delta.shape
    xs = extent[0] + (np.arange(nx) + 0.5) * (extent[1] - extent[0]) / nx
    ys = extent[2] + (np.arange(ny) + 0.5) * (extent[3] - extent[2]) / ny
    reduced = np.where(np.isfinite(delta), delta < dk_reduction, False).astype(float)
    handles = []
    if reduced.any():
        ax.contourf(xs, ys, reduced, levels=[0.5, 1.5], colors="none", hatches=["..."], zorder=3)
        ax.contour(xs, ys, reduced, levels=[0.5], colors="#1d1d1b", linewidths=1.0, zorder=4)
        from matplotlib.patches import Patch  # noqa: PLC0415

        handles.append(Patch(fill=False, hatch="...", ec="#1d1d1b",
                             label=f"Reducción (ΔK < {st.decimal_comma(dk_reduction)})"))
    handles += element_legend_handles(add_facade_elements(ax, scene))
    if wind_from_deg is not None:
        add_report_wind_badge(ax, wind_from_deg)
    if handles:
        fig.legend(handles=handles, loc="outside lower center", ncols=len(handles), fontsize=7,
                   frameon=False)
    ax.set_title(title or "Diferencia de K respecto al caso base")
    return fig, ax


def render_delta(root: str, target_dir: str, base_dir: str, scene: Scene | dict | None,
                 wind_from_deg: float | None, thresholds: dict, dpi: int = 150) -> list[dict]:
    """Write <target>/images/delta.png and register it in the target manifest."""
    target = storage.resolve(root, target_dir)
    delta = _field(target, "K") - _field(storage.resolve(root, base_dir), "K")
    extent = tuple(float(v) for v in np.load(target / "fields.npz")["extent"])
    if isinstance(scene, dict):
        scene = Scene.model_validate(scene)
    fig, _ = delta_figure(delta, extent, scene, wind_from_deg,
                          float(thresholds.get("dk_reduction", -0.1)))
    (target / "images").mkdir(exist_ok=True)
    save_png(fig, target / "images/delta.png", dpi)
    path = target / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    images = [i for i in manifest["images"] if i["name"] != "delta"]
    images.append({"name": "delta", "file": "images/delta.png"})
    manifest["images"] = images
    write_json(path, manifest)
    return images
