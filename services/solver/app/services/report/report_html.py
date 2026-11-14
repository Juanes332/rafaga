"""HTML of the A4 report (Spanish copy, WeasyPrint CSS paged media)."""

from html import escape
from pathlib import Path

from app.services.render.cardinal import format_decimal, format_dms
from app.services.render.map_style import LAWSON_LABELS, decimal_comma

FONTS = Path(__file__).with_name("fonts")
KIND_LABELS = {"plan2d": "Planta 2D", "section2d": "Corte vertical", "volume3d": "3D (LES)"}


def css(disclaimer: str) -> str:
    """Return the stylesheet with embedded fonts and the page footer."""
    lit, hk = (FONTS / "Literata.ttf").as_uri(), (FONTS / "HankenGrotesk.ttf").as_uri()
    note = disclaimer.replace('"', "'")
    return f"""
@font-face {{ font-family: 'Literata'; src: url('{lit}'); }}
@font-face {{ font-family: 'Hanken Grotesk'; src: url('{hk}'); }}
@page {{ size: A4; margin: 18mm 16mm 22mm 16mm;
  @bottom-left {{ content: "{note}"; font: 7.5pt 'Hanken Grotesk'; color: #555; }}
  @bottom-right {{ content: "Página " counter(page) " de " counter(pages); font: 7.5pt 'Hanken Grotesk'; }} }}
body {{ font: 10pt/1.45 'Literata'; color: #1d1d1b; }}
h1, h2, h3, th, .meta {{ font-family: 'Hanken Grotesk'; }}
h1 {{ font-size: 20pt; margin: 0 0 4pt; }} h2 {{ font-size: 13pt; margin-top: 16pt; }}
table {{ border-collapse: collapse; width: 100%; margin: 6pt 0; font-size: 9pt; }}
th, td {{ border-bottom: 0.5pt solid #bbb; padding: 3pt 5pt; text-align: left; }}
img {{ max-width: 100%; }} figure {{ margin: 6pt 0; page-break-inside: avoid; }}
.meta {{ color: #555; font-size: 9pt; }}"""


def num(value, digits: int = 2) -> str:
    """Return a number with decimal comma, or a dash."""
    return "—" if value is None else decimal_comma(float(value), digits)


def table(headers: list[str], rows: list[list[str]]) -> str:
    """Return an HTML table; cells are already escaped."""
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def site_text(pr: dict) -> str | None:
    """Return the site coordinates as decimal and DMS text, or None when unknown."""
    if pr.get("lat") is None or pr.get("lon") is None:
        return None
    lat, lon = float(pr["lat"]), float(pr["lon"])
    return f"{format_decimal(lat, lon)} ({format_dms(lat, lon)})"


def _coordinate_rows(pr: dict) -> list[list[str]]:
    """Return the decimal and DMS coordinate rows."""
    if pr.get("lat") is None or pr.get("lon") is None:
        return [["Coordenadas", "—"]]
    lat, lon = float(pr["lat"]), float(pr["lon"])
    return [["Coordenadas (decimales)", format_decimal(lat, lon)],
            ["Coordenadas (grados, minutos, segundos)", format_dms(lat, lon)],
            ["Norte", "Los mapas están orientados con el norte arriba (rosa de los vientos N, E, S, O)"]]


def project_section(snap: dict) -> str:
    """Return project, location and wind parameters."""
    pr, wind = snap.get("project", {}), snap.get("wind", {})
    rows = [
        *_coordinate_rows(pr),
        ["Altitud", f"{num(pr.get('elevation_m'), 0)} m ({escape(str(pr.get('elevation_source', '')))})"],
        ["Densidad del aire (ISA)", f"{num(pr.get('air_density_kg_m3'), 3)} kg/m³"],
        ["Altura de análisis", f"{num(pr.get('analysis_height_m'), 1)} m"],
        ["Fuente del viento", escape(str(wind.get("source", "")))],
        ["Periodo", f"{wind.get('period_years', '—')} años"],
        ["Categoría de terreno / z0", f"{escape(str(wind.get('terrain_category', '')))} / {num(wind.get('z0_m'), 2)} m"],
    ]
    return "<h2>Proyecto y emplazamiento</h2>" + table(["Parámetro", "Valor"], rows)


def parameters_section(snap: dict) -> str:
    """Return thresholds and the Lawson table."""
    th = snap.get("thresholds", {})
    rows = [["Umbral de aceleración", f"K &gt; {num(th.get('k_accel'))}"],
            ["Umbral de estancamiento", f"K &lt; {num(th.get('k_stagnation'))}"],
            ["Umbral de reducción", f"ΔK &lt; {num(th.get('dk_reduction'))}"]]
    law = snap.get("lawson") or {}
    lrows = [[escape(LAWSON_LABELS.get(c["class"], c["class"])), f"{num(c['threshold_ms'], 1)} m/s"]
             for c in law.get("comfort", [])]
    html = "<h2>Parámetros de evaluación</h2>" + table(["Criterio", "Valor"], rows)
    if lrows:
        pct = num(100 * law.get("exceedance", 0.05), 1)
        html += f"<h3>Tabla Lawson LDDC (excedencia {pct} %)</h3>" + table(["Clase", "Umbral"], lrows)
    return html
