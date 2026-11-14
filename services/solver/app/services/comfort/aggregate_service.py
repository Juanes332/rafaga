"""Lawson aggregate job: per-cell comfort classes for a study (SOL-12)."""

import json
import warnings
from pathlib import Path

import numpy as np

from app.configs.config import SOLVER_VERSION, Settings
from app.core.errors.solver_errors import InvalidPayloadError
from app.models.jobs.payload_parser import parse_payload
from app.models.jobs.payload_schemas import AggregatePayload
from app.services.comfort.lawson_model import (
    comfort_class, exceedance, gust_factor, sector_of, transfer_factor,
)
from app.services.comfort.lawson_outputs import write_outputs
from app.services.storage import output_dir_service as storage


def _read_field(result_dir: Path, name: str) -> np.ndarray | None:
    """Return a stored output field reshaped per its manifest, if present."""
    manifest = json.loads((result_dir / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["fields"]:
        if entry["name"] == name:
            dtype = "<f4" if entry["dtype"] == "float32" else np.uint8
            return np.fromfile(result_dir / entry["file"], dtype=dtype).reshape(entry["shape"])
    return None


def _sectors(p: AggregatePayload, root: str) -> tuple[list[dict], np.ndarray, np.ndarray]:
    """Group results by rose sector, averaging K (and I) inside a sector."""
    rose = p.rose["sectors"]
    centers = [s["center_deg"] for s in rose]
    grouped: dict[int, list[tuple[np.ndarray, np.ndarray | None]]] = {}
    solid = None
    shape = (p.output_grid.ny, p.output_grid.nx)
    for i, ref in enumerate(p.result_refs):
        folder = storage.resolve(root, ref["dir"])
        k = _read_field(folder, "K")
        if k is None or k.shape != shape:
            raise InvalidPayloadError("result is not on the study output grid",
                                      {"path": f"result_refs.{i}", "reason": "grid_mismatch"})
        ti = _read_field(folder, "ti")
        grouped.setdefault(sector_of(ref["wind_from_deg"], centers), []).append((k, ti))
        mask = _read_field(folder, "mask")
        solid = (mask == 1) if solid is None else solid | (mask == 1)
    t = transfer_factor(p.site["analysis_height_m"], p.site["z0_m"], p.site.get("z0_ref_m", 0.03),
                        p.site.get("blending_height_m", 60.0))
    out = []
    resolved = np.zeros(shape, dtype=bool)
    for idx, items in grouped.items():
        k = np.nanmean(np.stack([i[0] for i in items]), axis=0)
        ti, valid = _turbulence(items, k.shape, p.turbulence_intensity_default)
        resolved |= valid
        out.append(rose[idx] | {"K": np.nan_to_num(k, nan=0.0), "G": gust_factor(ti), "T": t})
    return out, solid, resolved


def _turbulence(items, shape, default: float) -> tuple[np.ndarray, np.ndarray]:
    """Return I (resolved 3D where finite, else the 2D default) and the valid mask."""
    tis = [i[1] for i in items if i[1] is not None and np.isfinite(i[1]).any()]
    if not tis:
        return np.full(shape, default), np.zeros(shape, dtype=bool)
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # all-NaN cells are expected
        ti = np.nanmean(np.stack(tis), axis=0)
    valid = np.isfinite(ti)
    return np.where(valid, ti, default), valid


def _gust_manifest(resolved: np.ndarray, solid: np.ndarray, default: float) -> dict:
    """Describe where the G = 1 floor is the effective gust factor."""
    fluid = ~solid
    return {
        "formula": "G = max(1, (1 + 3 I) / 1.85)", "floor": 1.0,
        "floor_applies_to": "cells_without_valid_ti",
        "note": "Cells without valid ti statistics use default_ti, whose G is the floor; "
                "resolved ti above (1.85 - 1) / 3 raises GEM above the mean.",
        "default_ti": default,
        "resolved_ti_cells": int((resolved & fluid).sum()),
        "default_ti_cells": int((~resolved & fluid).sum()),
    }


def run_aggregate(raw: dict, settings: Settings) -> dict:
    """Compute and publish the comfort result; return the comfort row."""
    p = parse_payload(AggregatePayload, raw)
    sectors, solid, resolved = _sectors(p, settings.data_dir)
    coverage = sum(s["frequency"] for s in sectors) / max(1.0 - p.rose.get("calm_fraction", 0.0), 1e-12)
    law = p.lawson
    comfort_p = [exceedance(c["threshold_ms"], sectors, coverage) for c in law["comfort"]]
    safety_p = [exceedance(s["threshold_ms"], sectors, coverage) for s in law["safety"]]
    classes = comfort_class(comfort_p, law["exceedance"])
    classes[solid] = 255
    safety = np.zeros(classes.shape, dtype=np.uint8)
    for bit, (prob, spec) in enumerate(zip(safety_p, law["safety"])):
        safety |= ((prob > spec["exceedance"]) & ~solid).astype(np.uint8) << bit
    final = storage.resolve(settings.data_dir, p.output_dir)
    tmp = storage.temp_dir(final)
    stack = np.stack(comfort_p + safety_p).astype(np.float32)
    stack[:, solid] = np.nan
    gust = _gust_manifest(resolved, solid, p.turbulence_intensity_default)
    row = write_outputs(tmp, p, classes, safety, stack, coverage, SOLVER_VERSION, gust)
    storage.publish(tmp, final)
    return row | {"dir": p.output_dir}
