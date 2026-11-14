"""Resolve and validate the inputs of an estimate or a study."""

from collections.abc import Mapping
from typing import Any

from app.core.errors.simulation_errors import (
    DirectionsRequiredError,
    LocationMissingError,
    RoseMissingError,
    WindMissingError,
)
from app.models.simulations.simulation_schemas import EstimateRequest


def ensure_located(inputs: Mapping[str, Any]) -> None:
    """Raise LocationMissingError unless location and density are set."""
    needed = ("lat", "lon", "air_density_kg_m3")
    if any(inputs[k] is None for k in needed):
        raise LocationMissingError()


def resolve_directions(inputs: Mapping[str, Any], body: EstimateRequest) -> list[float]:
    """Return the wind-from directions the study will run."""
    if body.kind == "section2d":
        return []
    if body.directions_deg:
        return [float(d) % 360 if d != 360 else 0.0 for d in body.directions_deg]
    if inputs["source"] == "manual" and inputs["manual_direction_deg"] is not None:
        return [float(inputs["manual_direction_deg"]) % 360]
    raise DirectionsRequiredError()


def resolve_u10(inputs: Mapping[str, Any], nominal: float) -> float:
    """Return U10: the manual value, or the nominal one for ERA5 roses."""
    if inputs["source"] == "era5":
        if inputs["rose"] is None:
            raise RoseMissingError()
        return nominal
    if inputs["manual_u10_ms"] is None:
        raise WindMissingError()
    return float(inputs["manual_u10_ms"])
