"""Atomic result directories under DATA_DIR (job-contract.md section 3, 5)."""

import shutil
from pathlib import Path

from app.core.errors.solver_errors import InvalidPayloadError, StorageError


def resolve(data_dir: str, relative: str) -> Path:
    """Return DATA_DIR/relative, refusing paths that escape the volume."""
    root = Path(data_dir).resolve()
    target = (root / relative).resolve()
    if root != target and root not in target.parents:
        raise InvalidPayloadError("path escapes the data volume", {"path": relative, "reason": "outside"})
    return target


def temp_dir(final: Path) -> Path:
    """Return a fresh <final>.tmp directory."""
    tmp = final.with_name(final.name + ".tmp")
    try:
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True)
    except OSError as exc:
        raise StorageError("cannot create the output directory", {"path": str(tmp)}) from exc
    return tmp


def publish(tmp: Path, final: Path) -> None:
    """Rename tmp onto final, replacing a previous attempt."""
    try:
        shutil.rmtree(final, ignore_errors=True)
        tmp.rename(final)
    except OSError as exc:
        raise StorageError("cannot publish the output directory", {"path": str(final)}) from exc


def discard(final: Path) -> None:
    """Remove the temporary and any partial final directory."""
    shutil.rmtree(final.with_name(final.name + ".tmp"), ignore_errors=True)
    shutil.rmtree(final, ignore_errors=True)
