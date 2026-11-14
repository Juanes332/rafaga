"""Shared mapping from a job's state to the export/report schemas."""

from collections.abc import Mapping
from typing import Any

DISCLAIMER = (
    "Herramienta de anteproyecto: compara alternativas, no sustituye un ensayo en túnel de viento."
)
_COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]


def job_view(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return status, progress and the structured error of the job."""
    error = None
    if row["error_code"]:
        error = {"code": row["error_code"], "message": row["error_message"] or row["error_code"]}
    return {"status": row["status"], "progress": float(row["progress"]), "error": error}


def wind_label(direction_deg: float | None) -> str:
    """Return the Spanish wind description with decimal comma."""
    if direction_deg is None:
        return "Viento sin dirección, U10 = 10,0 m/s"
    point = _COMPASS[int((direction_deg % 360) / 22.5 + 0.5) % 16]
    return f"Viento del {direction_deg:g}° ({point}), U10 = 10,0 m/s"
