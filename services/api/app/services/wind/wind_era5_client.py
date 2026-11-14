"""Fetch hourly ERA5 10 m wind from the Open-Meteo archive."""

from datetime import date, timedelta

import httpx

from app.configs.config import Settings
from app.core.errors.geo_errors import Era5UnavailableError

# ERA5 lags real time by days; stay clear of the incomplete tail.
ARCHIVE_LAG_DAYS = 10


async def fetch_hourly_wind(
    http: httpx.AsyncClient, settings: Settings, lat: float, lon: float, years: int
) -> tuple[list[float], list[float]]:
    """Return (speed_ms, direction_deg) hourly lists for the period.

    Only coordinates rounded to 0.1 degree leave the machine.
    """
    end = date.today() - timedelta(days=ARCHIVE_LAG_DAYS)
    start = end - timedelta(days=365 * years)
    params = {
        "latitude": round(lat, 1), "longitude": round(lon, 1),
        "start_date": start.isoformat(), "end_date": end.isoformat(),
        "hourly": "wind_speed_10m,wind_direction_10m", "wind_speed_unit": "ms",
    }
    try:
        resp = await http.get(settings.archive_url, params=params)
        resp.raise_for_status()
        hourly = resp.json()["hourly"]
        return hourly["wind_speed_10m"], hourly["wind_direction_10m"]
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise Era5UnavailableError(
            hint="Enter the wind direction and speed manually.") from exc
