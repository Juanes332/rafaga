"""Job state mapping and Spanish labels."""

from app.services.exports.job_view import job_view, wind_label
from app.services.reports.report_service import slugify


def test_wind_label_uses_spanish_points_and_comma() -> None:
    """270 degrees is O (oeste)."""
    assert wind_label(270.0) == "Viento del 270° (O), U10 = 10,0 m/s"
    assert wind_label(22.5).startswith("Viento del 22.5° (NNE)")


def test_job_view_maps_error() -> None:
    """A failed job exposes code and message, never details."""
    v = job_view({"status": "failed", "progress": 0, "error_code": "io_error", "error_message": None})
    assert v["error"] == {"code": "io_error", "message": "io_error"}


def test_slugify_strips_accents() -> None:
    """Slugs are ASCII with dashes."""
    assert slugify("Torre Ñandú 2!") == "torre-nandu-2"
    assert slugify("!!!") == "proyecto"
