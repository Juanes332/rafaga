"""Pydantic models of the location domain."""

from pydantic import BaseModel


class LocationRequest(BaseModel):
    """Body of PUT /projects/{id}/location; ranges checked in the service."""

    lat: float
    lon: float
    elevation_m: float | None = None
