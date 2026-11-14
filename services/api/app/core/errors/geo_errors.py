"""Failures of the geo, location, wind and tiles domains."""

from app.core.errors.error_contract import (
    ConflictError,
    UnavailableError,
    UnprocessableError,
)


class CoordinatesOutOfRangeError(UnprocessableError):
    """Latitude or longitude lies outside the valid range."""

    code = "coordinates_out_of_range"
    default_message = "Latitude must be within +-90 and longitude within +-180."


class ElevationUnavailableError(UnavailableError):
    """Open-Meteo elevation could not be obtained."""

    code = "elevation_unavailable"
    default_message = "Elevation service is unavailable."


class GeocodingUnavailableError(UnavailableError):
    """Open-Meteo geocoding failed and nothing is cached."""

    code = "geocoding_unavailable"
    default_message = "Geocoding service is unavailable."


class Era5UnavailableError(UnavailableError):
    """ERA5 archive failed and nothing is cached."""

    code = "era5_unavailable"
    default_message = "ERA5 wind data is unavailable."


class TileUnavailableError(UnavailableError):
    """Tile upstream failed and the tile is not cached."""

    code = "tile_unavailable"
    default_message = "Map tile is unavailable."


class LocationMissingError(ConflictError):
    """The project has no location yet."""

    code = "location_missing"
    default_message = "The project has no location."


class RoseMissingError(ConflictError):
    """ERA5 source requested but no wind rose is stored."""

    code = "rose_missing"
    default_message = "No ERA5 wind rose is stored for this project."


class TileCoordinateError(UnprocessableError):
    """Tile z/x/y outside the slippy-map grid."""

    code = "validation_error"
    default_message = "Tile coordinates are outside the map grid."
