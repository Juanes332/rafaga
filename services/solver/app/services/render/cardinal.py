"""Cardinal points and coordinate text in Spanish (West is 'O', Oeste)."""

from app.services.render.map_style import decimal_comma

POINTS = ("N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
          "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO")


def cardinal_name(deg: float) -> str:
    """Return the 16-point compass name of a bearing in degrees."""
    return POINTS[int(((deg % 360.0) + 11.25) // 22.5) % 16]


def _degrees(deg: float) -> str:
    """Return degrees with one decimal only when it is not an integer."""
    return decimal_comma(deg, 0) if abs(deg - round(deg)) < 1e-9 else decimal_comma(deg, 1)


def bearing_text(deg: float) -> str:
    """Return 'NE · 45°', degrees wrapped into [0, 360) after rounding."""
    shown = round(deg, 1) % 360.0
    return f"{cardinal_name(deg)} · {_degrees(shown)}°"


def wind_from_text(deg: float) -> str:
    """Return 'desde NE · 45°' for a meteorological wind direction."""
    return f"desde {bearing_text(deg)}"


def _dms(value: float) -> str:
    """Return degrees, minutes and whole seconds of an absolute angle."""
    total = round(abs(value) * 3600)
    d, rest = divmod(total, 3600)
    m, s = divmod(rest, 60)
    return f"{d}°{m:02d}′{s:02d}″"


def _negative(value: float, scale: float) -> bool:
    """Return True only when the value stays below zero at the printed precision."""
    return value < 0 and round(abs(value) * scale) > 0


def format_dms(lat: float, lon: float) -> str:
    """Return '4°36′35″ N · 74°04′54″ O'."""
    ns = "S" if _negative(lat, 3600) else "N"
    ew = "O" if _negative(lon, 3600) else "E"
    return f"{_dms(lat)} {ns} · {_dms(lon)} {ew}"


def format_decimal(lat: float, lon: float, digits: int = 5) -> str:
    """Return '4,60976° N · 74,08175° O'."""
    ns = "S" if _negative(lat, 10**digits) else "N"
    ew = "O" if _negative(lon, 10**digits) else "E"
    return f"{decimal_comma(abs(lat), digits)}° {ns} · {decimal_comma(abs(lon), digits)}° {ew}"
