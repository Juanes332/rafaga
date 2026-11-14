"""Hand-built scenes and heavy payloads gridded with the contract 3.2 rules."""

import math
from dataclasses import dataclass, field

from app.services.porous.porous_model import idelchik_zeta

ENVELOPE_M = 10.0
FAST = {"spinup_ft": 1.0, "min_avg_ft": 1.0, "max_avg_ft": 2.0,
        "check_every_ft": 0.25, "tolerance": 0.01, "consecutive": 3}


def _origin(kind: str, building: str, element: str | None = None) -> dict:
    """Return a primitive origin."""
    return {"kind": kind, "building_id": building, "element_id": element}


def rect(x0: float, y0: float, x1: float, y1: float) -> list[list[float]]:
    """Return a counter-clockwise rectangle ring."""
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


@dataclass
class SceneBuilder:
    """Accumulate buildings and facade primitives into a canonical scene."""

    z_a: float = 1.5
    z0: float = 1.0
    solids: list = field(default_factory=list)
    porous: list = field(default_factory=list)
    base: list = field(default_factory=list)

    def block(self, name: str, x0: float, y0: float, x1: float, y1: float, h: float) -> "SceneBuilder":
        """Add a base building."""
        self.solids.append({"id": f"b:{name}:t0", "origin": _origin("building", name),
                            "footprint": rect(x0, y0, x1, y1), "holes": [], "z_min": 0.0,
                            "z_max": h, "thin_axis_m": None})
        self.base.append((x0, y0, x1, y1, h))
        return self

    def canopy(self, name: str, x0: float, y0: float, x1: float, y1: float, z: float) -> "SceneBuilder":
        """Add a 0.3 m thick canopy slab at height z."""
        self.solids.append({"id": f"f:{name}:0", "origin": _origin("canopy", "b", name),
                            "footprint": rect(x0, y0, x1, y1), "holes": [], "z_min": z,
                            "z_max": z + 0.3, "thin_axis_m": 0.3})
        return self

    def fin(self, name: str, x0: float, y0: float, x1: float, y1: float, h: float) -> "SceneBuilder":
        """Add a full-height fin."""
        thin = min(x1 - x0, y1 - y0)
        self.solids.append({"id": f"f:{name}:{len(self.solids)}", "origin": _origin("fin", "b", name),
                            "footprint": rect(x0, y0, x1, y1), "holes": [], "z_min": 0.0,
                            "z_max": h, "thin_axis_m": thin})
        return self

    def screen(self, name: str, x0: float, y0: float, x1: float, y1: float, h: float,
               normal: tuple[float, float], porosity: float = 0.4) -> "SceneBuilder":
        """Add a porous screen (Idelchik loss coefficient)."""
        self.porous.append({"id": f"f:{name}:0", "origin": _origin("screen", "b", name),
                            "footprint": rect(x0, y0, x1, y1), "holes": [], "z_min": 0.0,
                            "z_max": h, "model": "screen", "porosity": porosity,
                            "loss_coefficient": float(idelchik_zeta(porosity)),
                            "normal": list(normal), "thickness_m": min(x1 - x0, y1 - y0)})
        return self

    def vegetation(self, name: str, x0: float, y0: float, x1: float, y1: float, h: float) -> "SceneBuilder":
        """Add a vegetation volume."""
        self.porous.append({"id": f"f:{name}:0", "origin": _origin("vegetation", "b", name),
                            "footprint": rect(x0, y0, x1, y1), "holes": [], "z_min": 0.0,
                            "z_max": h, "model": "vegetation", "lad_m2_m3": 1.0,
                            "drag_coefficient": 0.2})
        return self

    def build(self, phantom: tuple | None = None) -> dict:
        """Return the scene; `phantom` (x0,y0,x1,y1,h) sizes an empty domain."""
        boxes = self.base or [phantom]
        x0 = min(b[0] for b in boxes)
        y0 = min(b[1] for b in boxes)
        x1 = max(b[2] for b in boxes)
        y1 = max(b[3] for b in boxes)
        h = max(b[4] for b in boxes)
        return {"schema_version": "1.0", "units": "m", "frame": "local_enu",
                "source": {"project_id": "p", "alternative_id": "alt", "geometry_version": 1,
                           "compiled_at": "2026-01-01T00:00:00Z"},
                "analysis_height_m": self.z_a, "ground": {"z0_m": self.z0}, "h_max_m": h,
                "bounds": {"base_min": [x0, y0, 0.0], "base_max": [x1, y1, h],
                           "envelope_m": ENVELOPE_M},
                "solids": list(self.solids), "porous": list(self.porous), "warnings": []}


def _sim_grid(scene: dict, phi: float, dx: float, volume: bool) -> dict:
    """Return the wind-frame sim grid of contract 3.2 rule 2."""
    h = scene["h_max_m"]
    lo, hi, e = scene["bounds"]["base_min"], scene["bounds"]["base_max"], ENVELOPE_M
    corners = [(x, y) for x in (lo[0] - e, hi[0] + e) for y in (lo[1] - e, hi[1] + e)]
    r = math.radians(phi)
    d, n = (-math.sin(r), -math.cos(r)), (math.cos(r), -math.sin(r))
    xs = [cx * d[0] + cy * d[1] for cx, cy in corners]
    ys = [cx * n[0] + cy * n[1] for cx, cy in corners]
    x0, x1 = min(xs) - 5 * h, max(xs) + 15 * h
    y0, y1 = min(ys) - 5 * h, max(ys) + 5 * h
    z1 = 6 * h
    if volume:
        blockage = (max(ys) - min(ys)) * h / ((y1 - y0) * z1)
        f = 1.0 if blockage < 0.03 else math.sqrt(blockage / 0.03) * 1.001
        mid, half = (y0 + y1) / 2, (y1 - y0) / 2 * f
        y0, y1, z1 = mid - half, mid + half, z1 * f
    return {"frame": "wind", "wind_from_deg": phi, "axis_x": list(d), "axis_y": list(n),
            "origin": [x0, y0, 0.0], "dx_m": dx, "nx": math.ceil(round((x1 - x0) / dx, 6)),
            "ny": math.ceil(round((y1 - y0) / dx, 6)),
            "nz": math.ceil(round(z1 / dx, 6)) if volume else None}


def _output_grid(scene: dict, dx: float) -> dict:
    """Return the north-up output grid of contract 3.2 rule 3."""
    lo, hi = scene["bounds"]["base_min"], scene["bounds"]["base_max"]
    margin = ENVELOPE_M + 2 * scene["h_max_m"]
    ox = math.floor(round((lo[0] - margin) / dx, 6)) * dx
    oy = math.floor(round((lo[1] - margin) / dx, 6)) * dx
    return {"frame": "plan", "origin_x": ox, "origin_y": oy, "dx_m": dx,
            "nx": math.ceil(round((hi[0] + margin - ox) / dx, 6)),
            "ny": math.ceil(round((hi[1] + margin - oy) / dx, 6))}


def heavy_payload(scene: dict, kind: str = "plan2d", wind_from: float = 270.0, dx: float = 2.0,
                  convergence: dict | None = None, device: str = "auto") -> dict:
    """Return a self-contained plan2d / volume3d payload for a scene."""
    z0, z_a, kappa = scene["ground"]["z0_m"], scene["analysis_height_m"], 0.41
    ustar = kappa * 10.0 / math.log((10.0 + z0) / z0)
    return {
        "contract_version": 1, "job_kind": kind, "project_id": "p", "study_id": "s",
        "alternative_id": "alt", "output_dir": "results/p/s/j", "scene": scene, "section": None,
        "wind": {"wind_from_deg": wind_from, "u10_ms": 10.0, "z0_m": z0, "analysis_height_m": z_a,
                 "ustar_ms": ustar, "uref_za_ms": ustar / kappa * math.log((z_a + z0) / z0),
                 "kappa": kappa},
        "grid": {"sim": _sim_grid(scene, wind_from, dx, kind == "volume3d"),
                 "output": _output_grid(scene, dx)},
        "physics": {"inflow_perturbation": 0.02 if kind == "volume3d" else 0.0},
        "convergence": dict(convergence or FAST), "device": device,
        "render": {"dpi": 60, "k_accel": 1.2, "k_stagnation": 0.3},
    }
