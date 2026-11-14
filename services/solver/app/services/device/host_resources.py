"""cgroup-aware RAM and CPU figures as seen from inside the container."""

import math
import os
from pathlib import Path

_CGROUP = Path("/sys/fs/cgroup")


def _read_int(path: Path) -> int | None:
    """Return an integer file's value, or None when absent/unlimited."""
    try:
        text = path.read_text(encoding="utf-8").split()[0]
        return None if text == "max" else int(text)
    except (OSError, ValueError, IndexError):
        return None


def meminfo(root: Path = Path("/proc/meminfo")) -> dict[str, int]:
    """Return /proc/meminfo values in bytes."""
    values = {}
    for line in root.read_text(encoding="utf-8").splitlines():
        key, _, rest = line.partition(":")
        parts = rest.split()
        if parts:
            values[key] = int(parts[0]) * 1024
    return values


def ram_total_and_available(cgroup: Path = _CGROUP) -> tuple[int, int]:
    """Return (total, available) bytes honouring a cgroup memory limit."""
    info = meminfo()
    total, available = info["MemTotal"], info.get("MemAvailable", info["MemFree"])
    limit = _read_int(cgroup / "memory.max")
    if limit is not None and limit < total:
        used = _read_int(cgroup / "memory.current") or 0
        total, available = limit, min(available, max(limit - used, 0))
    return total, available


def ram_budget(fraction: float = 0.6) -> int:
    """Return the CPU lattice budget: 0.6 x MemAvailable (ADR-10)."""
    return int(fraction * ram_total_and_available()[1])


def cpu_cores(cgroup: Path = _CGROUP) -> int:
    """Return usable cores: affinity capped by a cgroup CPU quota."""
    cores = len(os.sched_getaffinity(0))
    try:
        quota, period = (cgroup / "cpu.max").read_text(encoding="utf-8").split()
        if quota != "max":
            cores = min(cores, max(1, math.floor(int(quota) / int(period))))
    except (OSError, ValueError):
        pass
    return cores
