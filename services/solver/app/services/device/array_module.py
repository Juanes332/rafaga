"""The one array-module abstraction: CuPy on GPU, NumPy on CPU (ADR-03)."""

from types import ModuleType
from typing import Any, Literal

import numpy as np

Device = Literal["cpu", "gpu"]


def cupy_or_none() -> ModuleType | None:
    """Return the cupy module when it imports and sees a device, else None."""
    try:
        import cupy  # noqa: PLC0415  (optional dependency, absent on CPU hosts)

        if cupy.cuda.runtime.getDeviceCount() < 1:
            return None
        return cupy
    except Exception:  # noqa: BLE001  (any CUDA/driver failure means "no GPU")
        return None


def get_xp(device: Device) -> ModuleType:
    """Return cupy for 'gpu' and numpy for 'cpu'."""
    if device == "cpu":
        return np
    cupy = cupy_or_none()
    if cupy is None:
        raise RuntimeError("cupy is not usable on this host")
    return cupy


def to_host(array: Any) -> np.ndarray:
    """Return a NumPy copy of a NumPy or CuPy array."""
    if isinstance(array, np.ndarray):
        return array
    return array.get()
