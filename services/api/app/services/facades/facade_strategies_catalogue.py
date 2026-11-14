"""Single source of facade strategy ranges, defaults and clamping."""

from typing import Any

# Each parameter: key, unit, min, max, default (None means "building height").
def _p(key: str, unit: str, lo: float, hi: float, default: float | None) -> dict[str, Any]:
    """Build one parameter spec with its help key."""
    return {"key": key, "unit": unit, "min": lo, "max": hi, "default": default,
            "help_key": f"facade.param.{key}.help"}


STRATEGIES: dict[str, list[dict[str, Any]]] = {
    "screen": [
        _p("porosity", "1", 0.05, 0.95, 0.4),
        _p("height_m", "m", 0.5, 50, 3.0),
        _p("offset_m", "m", 0, 5, 0.5),
    ],
    "fins": [
        _p("depth_m", "m", 0.1, 3.0, 0.5),
        _p("pitch_m", "m", 0.3, 10, 1.0),
        _p("thickness_m", "m", 0.05, 0.5, 0.15),
        _p("height_m", "m", 1, 500, None),
    ],
    "canopy": [
        _p("overhang_m", "m", 0.5, 6.0, 2.0),
        _p("height_m", "m", 2.5, 10, 3.5),
        _p("thickness_m", "m", 0.3, 0.3, 0.3),
    ],
    "setback": [
        _p("setback_m", "m", 0.1, 5.0, 1.0),
        _p("floor_height_m", "m", 2.5, 6.0, 3.0),
        _p("start_floor", "1", 1, 100, 1),
    ],
    "vegetation": [
        _p("lad_m2_m3", "m2/m3", 0.1, 5.0, 1.0),
        _p("height_m", "m", 1, 30, 8.0),
        _p("width_m", "m", 0.5, 5.0, 3.0),
        _p("offset_m", "m", 0, 5.0, 1.0),
    ],
}
INTEGER_KEYS = {"start_floor"}


def _number(value: Any) -> float:
    """Return a finite float or raise InvalidFacadeParamsError."""
    from app.core.errors.alternative_errors import InvalidFacadeParamsError

    if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value:
        raise InvalidFacadeParamsError()
    return float(value)


def _clamp_one(spec: dict[str, Any], value: Any) -> tuple[Any, dict[str, Any] | None]:
    """Clamp one value; return it with its adjustment, if any."""
    if value is None:
        return spec["default"], None
    requested = _number(value)
    applied = min(max(requested, spec["min"]), spec["max"])
    if spec["key"] in INTEGER_KEYS:
        applied = int(round(applied))
    adjustment = None
    if applied != requested and spec["key"] not in INTEGER_KEYS:
        reason = "below_minimum" if requested < spec["min"] else "above_maximum"
        adjustment = {"field": spec["key"], "requested": requested,
                      "applied": float(applied), "reason": reason}
    return applied, adjustment


def clamp_params(
    type_: str, params: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return complete params with defaults applied, plus adjustments.

    Raises InvalidFacadeParamsError for unknown keys or non-numbers.
    """
    from app.core.errors.alternative_errors import InvalidFacadeParamsError

    specs = {s["key"]: s for s in STRATEGIES[type_]}
    if set(params) - set(specs):
        raise InvalidFacadeParamsError()
    result: dict[str, Any] = {}
    adjustments: list[dict[str, Any]] = []
    for key, spec in specs.items():
        value, adjustment = _clamp_one(spec, params.get(key))
        result[key] = value
        if adjustment:
            adjustments.append(adjustment)
    return result, adjustments
