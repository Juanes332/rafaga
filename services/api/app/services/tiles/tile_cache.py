"""On-disk LRU tile cache with per-tile expiry sidecars."""

import json
import os
import time
from pathlib import Path

MIN_TTL_S = 7 * 86400


def tile_path(root: Path, z: int, x: int, y: int) -> Path:
    """Return the cache file path of a tile."""
    return root / str(z) / str(x) / f"{y}.png"


def parse_ttl(cache_control: str | None) -> int:
    """Return the TTL honouring max-age, never below seven days."""
    ttl = 0
    for part in (cache_control or "").split(","):
        name, _, value = part.strip().partition("=")
        if name.lower() == "max-age" and value.strip().isdigit():
            ttl = int(value)
    return max(ttl, MIN_TTL_S)


def read_tile(path: Path) -> tuple[bytes, bool] | None:
    """Return (bytes, fresh) and mark the tile used, or None if absent."""
    try:
        data = path.read_bytes()
        expires = json.loads(path.with_suffix(".json").read_text())["expires"]
    except (OSError, ValueError, KeyError):
        return None if not path.exists() else (data, False)
    os.utime(path)
    return data, expires > time.time()


def write_tile(path: Path, data: bytes, ttl_s: int) -> None:
    """Persist a tile and its expiry sidecar."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.with_suffix(".json").write_text(json.dumps({"expires": time.time() + ttl_s}))


def evict(root: Path, max_bytes: int) -> int:
    """Delete least-recently-used tiles until under the cap; return count."""
    files = [(p.stat().st_mtime, p.stat().st_size, p) for p in root.rglob("*.png")]
    total = sum(size for _, size, _ in files)
    removed = 0
    for _, size, path in sorted(files):
        if total <= max_bytes:
            break
        path.unlink(missing_ok=True)
        path.with_suffix(".json").unlink(missing_ok=True)
        total -= size
        removed += 1
    return removed
