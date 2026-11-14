"""Pydantic models of the geo domain."""

from typing import Literal

from pydantic import BaseModel


class GeoResult(BaseModel):
    """One geocoding match."""

    name: str
    admin1: str | None = None
    country: str | None = None
    lat: float
    lon: float
    elevation_m: float | None = None


class ElevationResponse(BaseModel):
    """Elevation with its ISA air density."""

    elevation_m: float
    air_density_kg_m3: float
    source: Literal["open_meteo"] = "open_meteo"


class TerrainCategory(BaseModel):
    """One BR-08 roughness category."""

    key: str
    label_key: str
    z0_m: float
    default: bool
