"""Scaled-down heavy payloads built from the contract examples."""

import copy
import math

from tests.support.contracts import example

FAST_CONVERGENCE = {"spinup_ft": 0.5, "min_avg_ft": 0.5, "max_avg_ft": 1.0,
                    "check_every_ft": 0.25, "tolerance": 0.01, "consecutive": 3}


def plan_payload(dx: float = 4.0, wind_from: float = 270.0, device: str = "auto",
                 convergence: dict | None = None, kind: str = "plan2d") -> dict:
    """Return the example plan2d/volume3d payload regridded at dx."""
    raw = copy.deepcopy(example("job.volume3d.example" if kind == "volume3d" else "job.plan2d.example"))
    h = raw["scene"]["h_max_m"]
    phi = math.radians(wind_from)
    d, n = (-math.sin(phi), -math.cos(phi)), (math.cos(phi), -math.sin(phi))
    corners = [(x, y) for x in (-20.0, 20.0) for y in (-25.0, 25.0)]
    xs = [cx * d[0] + cy * d[1] for cx, cy in corners]
    ys = [cx * n[0] + cy * n[1] for cx, cy in corners]
    x0, x1 = min(xs) - 5 * h, max(xs) + 15 * h
    y0, y1 = min(ys) - 5 * h, max(ys) + 5 * h
    raw["grid"]["sim"].update({
        "wind_from_deg": wind_from, "axis_x": list(d), "axis_y": list(n),
        "origin": [x0, y0, 0.0], "dx_m": dx, "nx": math.ceil((x1 - x0) / dx),
        "ny": math.ceil((y1 - y0) / dx), "nz": math.ceil(6 * h / dx) if kind == "volume3d" else None,
    })
    ext = 10 + 2 * h
    ox, oy = math.floor((-10 - ext) / dx) * dx, math.floor((-15 - ext) / dx) * dx
    raw["grid"]["output"] = {"frame": "plan", "origin_x": ox, "origin_y": oy, "dx_m": dx,
                             "nx": math.ceil((10 + ext - ox) / dx), "ny": math.ceil((15 + ext - oy) / dx)}
    raw["wind"]["wind_from_deg"] = wind_from
    raw["convergence"] = dict(convergence or FAST_CONVERGENCE)
    raw["device"] = device
    return raw


def section_payload(dx: float = 4.0, device: str = "auto") -> dict:
    """Return a section2d payload cutting the example building west-east."""
    raw = copy.deepcopy(example("job.plan2d.example"))
    h = raw["scene"]["h_max_m"]
    p0, p1 = (-60.0, 0.0), (60.0, 0.0)
    ns, nz = math.ceil((120 + 20 * h) / dx), math.ceil(6 * h / dx)
    raw.update({"job_kind": "section2d", "section": {"p0": list(p0), "p1": list(p1)}, "device": device})
    raw["grid"] = {
        "sim": {"frame": "section", "wind_from_deg": 270.0, "origin": [-5 * h, 0.0], "dx_m": dx,
                "nx": ns, "ny": None, "nz": nz},
        "output": {"frame": "section", "s0": -5 * h, "dx_m": dx, "ns": ns, "nz": nz},
    }
    raw["convergence"] = dict(FAST_CONVERGENCE)
    return raw
