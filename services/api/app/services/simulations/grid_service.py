"""Simulation and output grids exactly as job-contract.md section 3.2."""

import math
from collections.abc import Mapping, Sequence
from typing import Any

BLOCKAGE_LIMIT = 0.03
UPSTREAM_H, DOWNSTREAM_H, LATERAL_H, TOP_H = 5.0, 15.0, 5.0, 6.0
# The 3D volume top is lower to keep 25 M nodes inside 8 GB of VRAM (BL-02).
TOP_H_VOLUME = 5.0


def _cells(length: float, dx: float) -> int:
    """Return ceil(length / dx), robust to float noise."""
    return math.ceil(round(length / dx, 6))


def frame_axes(phi_deg: float) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return the flow-advance axis d and the lateral axis n in ENU."""
    phi = math.radians(phi_deg)
    d = (-math.sin(phi), -math.cos(phi))
    n = (math.cos(phi), -math.sin(phi))
    return (round(d[0], 9) + 0.0, round(d[1], 9) + 0.0), (round(n[0], 9) + 0.0, round(n[1], 9) + 0.0)


def base_box(scene: Mapping[str, Any]) -> tuple[float, float, float, float]:
    """Return the base bounding box widened by the facade envelope."""
    lo, hi = scene["bounds"]["base_min"], scene["bounds"]["base_max"]
    e = scene["bounds"]["envelope_m"]
    return lo[0] - e, lo[1] - e, hi[0] + e, hi[1] + e


def _project(corners: Sequence[tuple[float, float]], axis: tuple[float, float]) -> list[float]:
    """Return the scalar projection of points on an axis."""
    return [x * axis[0] + y * axis[1] for x, y in corners]


def _stretch_for_blockage(ly: float, lz: float, width: float, h: float) -> float:
    """Return the factor that brings blockage under the 3 percent limit."""
    blockage = width * h / (ly * lz)
    if blockage < BLOCKAGE_LIMIT:
        return 1.0
    return math.sqrt(blockage / BLOCKAGE_LIMIT) * 1.001


def sim_grid_wind(
    scene: Mapping[str, Any], phi_deg: float, dx: float, volume: bool
) -> dict[str, Any]:
    """Return the wind-frame simulation grid for one direction."""
    h = scene["h_max_m"]
    x0b, y0b, x1b, y1b = base_box(scene)
    corners = [(x0b, y0b), (x1b, y0b), (x1b, y1b), (x0b, y1b)]
    d, n = frame_axes(phi_deg)
    xs, ys = _project(corners, d), _project(corners, n)
    x0, x1 = min(xs) - UPSTREAM_H * h, max(xs) + DOWNSTREAM_H * h
    y0, y1 = min(ys) - LATERAL_H * h, max(ys) + LATERAL_H * h
    z1 = (TOP_H_VOLUME if volume else TOP_H) * h
    if volume:
        f = _stretch_for_blockage(y1 - y0, z1, max(ys) - min(ys), h)
        mid, half = (y0 + y1) / 2, (y1 - y0) / 2 * f
        y0, y1, z1 = mid - half, mid + half, z1 * f
    return {
        "frame": "wind", "wind_from_deg": float(phi_deg),
        "axis_x": list(d), "axis_y": list(n),
        "origin": [round(x0, 6), round(y0, 6), 0.0], "dx_m": dx,
        "nx": _cells(x1 - x0, dx), "ny": _cells(y1 - y0, dx),
        "nz": _cells(z1, dx) if volume else None,
    }


def output_grid_plan(scene: Mapping[str, Any], dx: float) -> dict[str, Any]:
    """Return the plan output grid shared by every direction and alternative."""
    lo, hi = scene["bounds"]["base_min"], scene["bounds"]["base_max"]
    margin = scene["bounds"]["envelope_m"] + 2 * scene["h_max_m"]
    ox = math.floor(round((lo[0] - margin) / dx, 6)) * dx
    oy = math.floor(round((lo[1] - margin) / dx, 6)) * dx
    return {
        "frame": "plan", "origin_x": round(ox, 6), "origin_y": round(oy, 6), "dx_m": dx,
        "nx": _cells(hi[0] + margin - ox, dx), "ny": _cells(hi[1] + margin - oy, dx),
    }


def section_wind_from_deg(p0: Sequence[float], p1: Sequence[float]) -> float:
    """Return the bearing of p1 to p0, the direction the wind comes from."""
    return math.degrees(math.atan2(p0[0] - p1[0], p0[1] - p1[1])) % 360.0


def section_grids(
    scene: Mapping[str, Any], p0: Sequence[float], p1: Sequence[float], dx: float
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the (sim, output) grids of a vertical section."""
    h = scene["h_max_m"]
    s0 = -UPSTREAM_H * h
    ns = _cells(math.dist(p0, p1) + 20 * h, dx)
    nz = _cells(TOP_H * h, dx)
    sim = {
        "frame": "section", "wind_from_deg": round(section_wind_from_deg(p0, p1), 6),
        "origin": [s0, 0.0], "dx_m": dx, "nx": ns, "ny": None, "nz": nz,
    }
    return sim, {"frame": "section", "s0": s0, "dx_m": dx, "ns": ns, "nz": nz}


def node_count(sim: Mapping[str, Any]) -> int:
    """Return the number of lattice nodes of a simulation grid."""
    if sim["frame"] == "section":
        return sim["nx"] * sim["nz"]
    return sim["nx"] * sim["ny"] * (sim["nz"] or 1)
