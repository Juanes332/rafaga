"""Live GPU facts through CuPy (never imported on CPU-only paths)."""

from dataclasses import dataclass

from app.services.device.array_module import cupy_or_none


@dataclass(frozen=True)
class GpuInfo:
    """Name and memory of device 0."""

    name: str
    total_bytes: int
    free_bytes: int


def gpu_info() -> GpuInfo | None:
    """Return the GPU's name and memory, or None without a usable GPU."""
    cp = cupy_or_none()
    if cp is None:
        return None
    try:
        props = cp.cuda.runtime.getDeviceProperties(0)
        free, total = cp.cuda.runtime.memGetInfo()
        name = props["name"].decode() if isinstance(props["name"], bytes) else str(props["name"])
        return GpuInfo(name, int(total), int(free))
    except Exception:  # noqa: BLE001  (driver errors mean "no GPU")
        return None
