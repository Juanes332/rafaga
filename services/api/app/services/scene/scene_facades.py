"""Expand one facade element into solid and porous prisms."""

import math
from typing import Any

from app.services.scene.scene_geometry import Point, edge_rectangle

Frame = tuple[Point, Point, Point, float]
Expansion = tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]]]
SCREEN_THICKNESS_M = 0.1
CANOPY_THICKNESS_M = 0.3


def screen_loss_coefficient(porosity: float) -> float:
    """Return the Idelchik thin perforated plate coefficient (ADR-13)."""
    b = porosity
    return round(((0.707 * math.sqrt(1 - b) + 1 - b) / b) ** 2, 4)


def _origin(kind: str, building_id: str, element_id: str) -> dict[str, Any]:
    """Build the origin block of a facade primitive."""
    return {"kind": kind, "building_id": building_id, "element_id": element_id}


def _prism(el: dict[str, Any], kind: str, k: int, ring: list[list[float]], z0: float, z1: float) -> dict[str, Any]:
    """Build the common prism fields."""
    return {
        "id": f"f:{el['id']}:{k}", "origin": _origin(kind, el["building_id"], el["id"]),
        "footprint": ring, "z_min": round(z0, 6), "z_max": round(z1, 6),
    }


def _capped(el: dict[str, Any], top: float, building_h: float, warnings: list[dict[str, str]]) -> float:
    """Cap a top elevation at the building height, reporting the cut."""
    if top > building_h:
        warnings.append({"code": "above_building_clamped", "ref": el["id"]})
        return building_h
    return top


def _screen(el: dict[str, Any], f: Frame, bh: float, **_: Any) -> Expansion:
    """Expand a porous screen parallel to the edge."""
    a, u, n, length = f
    p, warnings = el["params"], []
    off = p["offset_m"]
    ring = edge_rectangle(a, u, n, 0, length, off, off + SCREEN_THICKNESS_M)
    prism = _prism(el, "screen", 0, ring, 0.0, _capped(el, p["height_m"], bh, warnings))
    prism.update(model="screen", porosity=p["porosity"], thickness_m=SCREEN_THICKNESS_M,
                 loss_coefficient=screen_loss_coefficient(p["porosity"]),
                 normal=[round(n[0], 6), round(n[1], 6)])
    return [], [prism], warnings


def _fins(el: dict[str, Any], f: Frame, bh: float, **_: Any) -> Expansion:
    """Expand perpendicular fins spaced along the edge."""
    a, u, n, length = f
    p, warnings = el["params"], []
    th, pitch = p["thickness_m"], p["pitch_m"]
    top = _capped(el, p["height_m"] if p["height_m"] is not None else bh, bh, warnings)
    solids = []
    for k in range(int((length - th) // pitch) + 1):
        c = pitch / 2 + k * pitch
        if c + th / 2 > length:
            break
        ring = edge_rectangle(a, u, n, c - th / 2, c + th / 2, 0, p["depth_m"])
        s = _prism(el, "fin", k, ring, 0.0, top)
        s["thin_axis_m"] = th
        solids.append(s)
    if not solids:
        warnings.append({"code": "element_degenerate", "ref": el["id"]})
    return solids, [], warnings


def _canopy(el: dict[str, Any], f: Frame, bh: float, **_: Any) -> Expansion:
    """Expand a slab that overhangs the edge."""
    a, u, n, length = f
    p, warnings = el["params"], []
    z1 = _capped(el, p["height_m"] + CANOPY_THICKNESS_M, bh, warnings)
    z0 = max(0.0, min(p["height_m"], z1 - CANOPY_THICKNESS_M))
    ring = edge_rectangle(a, u, n, 0, length, 0, p["overhang_m"])
    s = _prism(el, "canopy", 0, ring, z0, z1)
    s["thin_axis_m"] = CANOPY_THICKNESS_M
    return [s], [], warnings


def _vegetation(el: dict[str, Any], f: Frame, bh: float, cd: float, **_: Any) -> Expansion:
    """Expand a drag volume strip along the edge."""
    a, u, n, length = f
    p = el["params"]
    ring = edge_rectangle(a, u, n, 0, length, p["offset_m"], p["offset_m"] + p["width_m"])
    prism = _prism(el, "vegetation", 0, ring, 0.0, p["height_m"])
    prism.update(model="vegetation", lad_m2_m3=p["lad_m2_m3"], drag_coefficient=cd)
    return [], [prism], []


_EXPANDERS = {"screen": _screen, "fins": _fins, "canopy": _canopy, "vegetation": _vegetation}


def expand_element(el: dict[str, Any], frame: Frame, building_h: float, z_a: float, cd: float) -> Expansion:
    """Return the primitives and warnings of a non-setback element."""
    solids, porous, warnings = _EXPANDERS[el["type"]](el, frame, building_h, cd=cd)
    top = max([s["z_max"] for s in solids + porous], default=z_a)
    if top < z_a:
        warnings.append({"code": "below_analysis_height", "ref": el["id"]})
    return solids, porous, warnings
