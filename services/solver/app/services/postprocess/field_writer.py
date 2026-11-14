"""Write raw little-endian fields, the npz bundle and stats (job-contract 5)."""

import json
from pathlib import Path

import numpy as np

from app.services.postprocess.output_fields import OutputFields


def write_fields(fields: OutputFields, out_dir: Path) -> list[dict]:
    """Write fields/<name>.f32 and fields/mask.u8; return manifest entries."""
    target = out_dir / "fields"
    target.mkdir(parents=True, exist_ok=True)
    entries = []
    for name, arr in fields.arrays.items():
        file = f"fields/{name}.f32"
        arr.astype("<f4").tofile(out_dir / file)
        entries.append({"name": name, "file": file, "dtype": "float32", "shape": list(arr.shape)})
    fields.mask.astype(np.uint8).tofile(out_dir / "fields/mask.u8")
    entries.append({"name": "mask", "file": "fields/mask.u8", "dtype": "uint8",
                    "shape": list(fields.mask.shape)})
    np.savez_compressed(out_dir / "fields.npz", mask=fields.mask, dx_m=fields.dx_m,
                        extent=np.asarray(fields.extent), **fields.arrays)
    return entries


def field_stats(fields: OutputFields) -> dict:
    """Return {k_mean, k_max, k_p95, fluid_area_m2} over fluid cells."""
    k = fields.arrays["K"]
    finite = k[np.isfinite(k)]
    area = float((fields.mask != 1).sum() * fields.dx_m**2)
    if finite.size == 0:
        return {"k_mean": None, "k_max": None, "k_p95": None, "fluid_area_m2": area}
    return {"k_mean": round(float(finite.mean()), 6), "k_max": round(float(finite.max()), 6),
            "k_p95": round(float(np.percentile(finite, 95)), 6), "fluid_area_m2": area}


def write_json(path: Path, data: dict) -> None:
    """Write UTF-8 JSON (NaN-free by construction)."""
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
