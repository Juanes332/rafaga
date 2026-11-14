"""Files, areas and the lawson.png of an aggregate result (SOL-12)."""

from pathlib import Path

import numpy as np

from app.models.jobs.payload_schemas import AggregatePayload
from app.services.postprocess.field_writer import write_json
from app.services.render.map_figure import draw_lawson, new_map, save_png

_CLASSES = "ABCDE"


def class_areas(classes: np.ndarray, dx: float) -> list[dict]:
    """Return [{class, area_m2, percent}] over fluid cells."""
    fluid = classes != 255
    total = max(int(fluid.sum()), 1)
    return [{"class": c, "area_m2": float((classes == i).sum() * dx * dx),
             "percent": round(100.0 * (classes == i).sum() / total, 3)}
            for i, c in enumerate(_CLASSES)]


def safety_areas(safety: np.ndarray, fluid: np.ndarray, specs: list[dict], dx: float) -> list[dict]:
    """Return [{label, area_m2, percent}] per safety criterion."""
    total = max(int(fluid.sum()), 1)
    out = []
    for bit, spec in enumerate(specs):
        hit = (safety >> bit) & 1
        out.append({"label": spec["key"], "area_m2": float(hit.sum() * dx * dx),
                    "percent": round(100.0 * hit.sum() / total, 3)})
    return out


def write_outputs(out: Path, p: AggregatePayload, classes, safety, stack, coverage: float,
                  version: str, gust: dict | None = None) -> dict:
    """Write fields, image and manifest; return the comfort_results row."""
    (out / "fields").mkdir(parents=True)
    (out / "images").mkdir()
    classes.tofile(out / "fields/lawson_class.u8")
    safety.tofile(out / "fields/safety.u8")
    stack.astype("<f4").tofile(out / "fields/exceedance.f32")
    g = p.output_grid
    shape = list(classes.shape)
    fields = [
        {"name": "lawson_class", "file": "fields/lawson_class.u8", "dtype": "uint8", "shape": shape},
        {"name": "safety", "file": "fields/safety.u8", "dtype": "uint8", "shape": shape},
        {"name": "exceedance", "file": "fields/exceedance.f32", "dtype": "float32",
         "shape": [stack.shape[0]] + shape},
    ]
    extent = (g.origin_x, g.origin_x + g.nx * g.dx_m, g.origin_y, g.origin_y + g.ny * g.dx_m)
    fig, ax = new_map(extent)
    draw_lawson(fig, ax, classes, extent)
    ax.set_title("Confort peatonal (criterio Lawson LDDC)")
    save_png(fig, out / "images/lawson.png", 150)
    row = {
        "lawson_hash": p.lawson_hash, "lawson": p.lawson, "coverage": round(coverage, 6),
        "partial": coverage < 0.95, "class_areas": class_areas(classes, g.dx_m),
        "safety_areas": safety_areas(safety, classes != 255, p.lawson["safety"], g.dx_m),
        "fields": fields, "images": [{"name": "lawson", "file": "images/lawson.png"}],
    }
    write_json(out / "manifest.json", row | {"contract_version": 1, "solver_version": version,
                                             "study_id": p.study_id,
                                             "gust_factor": gust})
    return row
