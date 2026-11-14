"""Allow-listed access to the files of a result (never by user path)."""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np

from app.configs.config import Settings


def entry_by_name(entries: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    """Return the entry whose logical name equals the requested one."""
    return next((e for e in entries if e["name"] == name), None)


def image_file_name(entry: dict[str, Any]) -> str:
    """Return the public image name used by GET /images/{image_name} (e.g. ``k.png``)."""
    return f"{entry['name']}.png"


def warning_code(warning: Any) -> str:
    """Return the code of a solver warning stored as ``{code, ref}`` or as a bare string."""
    return warning["code"] if isinstance(warning, dict) else str(warning)


def safe_path(settings: Settings, result: Mapping[str, Any], relative: str) -> Path | None:
    """Resolve a stored relative path inside the result directory, or None."""
    base = (Path(settings.data_dir) / result["dir"]).resolve()
    target = (base / relative).resolve()
    if not target.is_relative_to(base) or not target.is_file():
        return None
    return target


def load_field(settings: Settings, result: Mapping[str, Any], name: str) -> np.ndarray | None:
    """Load a float32 field as a 2D array, or None when unavailable."""
    entry = entry_by_name(result["fields"], name)
    path = safe_path(settings, result, entry["file"]) if entry else None
    if entry is None or path is None:
        return None
    return np.fromfile(path, dtype="<f4").reshape(entry["shape"])
