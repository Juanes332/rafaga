"""PDF report job rendered with WeasyPrint (SOL-14)."""

from html import escape

from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

from app.configs.config import Settings
from app.models.jobs.payload_parser import parse_payload
from app.models.jobs.payload_schemas import ReportPayload
from app.services.render.cardinal import wind_from_text
from app.services.render.render_service import DEFAULT_DISCLAIMER, load_field
from app.services.report.report_charts import k_map, lawson_map, rose_chart
from app.services.report.report_comparison import comparison_section, load_scene
from app.services.report.report_html import (
    KIND_LABELS,
    css,
    num,
    parameters_section,
    project_section,
    site_text,
    table,
)
from app.services.storage import output_dir_service as storage

# BL-12: model-confidence note, merged with the FR-48 footer disclaimer (same wording as the web).
MODEL_NOTE = (
    "Ráfaga sirve para comparar alternativas y detectar zonas incómodas en etapas de diseño. "
    "No reemplaza un ensayo en túnel de viento para proyectos críticos."
)


def _extent(root: str, result_dir: str) -> tuple[float, float, float, float]:
    """Return the plot extent stored with a result's npz bundle."""
    import numpy as np  # noqa: PLC0415

    bundle = np.load(storage.resolve(root, result_dir) / "fields.npz")
    return tuple(float(v) for v in bundle["extent"])


def _study(root: str, study: dict) -> str:
    """Return one study's maps and area tables."""
    name = escape(str(study.get("alternative_name", "")))
    kind = KIND_LABELS.get(study.get("kind"), study.get("kind"))
    html = f"<h2>{name}</h2><p class='meta'>{kind} · celda {num(study.get('dx_m'), 2)} m · {escape(str(study.get('device', '')).upper())}</p>"
    for res in study.get("results", []):
        conv = "convergió" if res.get("convergence", {}).get("converged") else "no convergió del todo"
        wind = res.get("wind_from_deg")
        title = f"Viento {wind_from_text(float(wind)) if wind is not None else '—'} · {conv}"
        uri = k_map(load_field(root, res["result_dir"], "K"), _extent(root, res["result_dir"]), title,
                    load_scene(root, res["result_dir"]), None if wind is None else float(wind))
        html += f"<figure><img src='{uri}'/></figure>"
    zones = study.get("zone_areas") or {}
    rows = [[label, f"{num(zones[key].get('area_m2'), 0)} m²", f"{num(zones[key].get('percent'), 1)} %"]
            for key, label in (("acceleration", "Aceleración"), ("stagnation", "Estancamiento"),
                               ("reduction", "Reducción")) if key in zones]
    if rows:
        html += "<h3>Áreas por zona</h3>" + table(["Zona", "Área", "Porcentaje"], rows)
    return html + _comfort(root, study)


def _comfort(root: str, study: dict) -> str:
    """Return the Lawson map and class table when the study has one."""
    areas = study.get("comfort_areas") or {}
    html = ""
    if study.get("comfort_dir") and study.get("results"):
        classes = load_field(root, study["comfort_dir"], "lawson_class")
        html += f"<figure><img src='{lawson_map(classes, _extent(root, study['results'][0]['result_dir']), 'Confort Lawson')}'/></figure>"
    if areas.get("class_areas"):
        cov = num(100 * areas.get("coverage", 0), 1)
        flag = " (parcial)" if areas.get("partial") else ""
        rows = [[c["class"], f"{num(c.get('area_m2'), 0)} m²", f"{num(c.get('percent'), 1)} %"]
                for c in areas["class_areas"]]
        html += f"<h3>Confort Lawson · cobertura {cov} %{flag}</h3>" + table(["Clase", "Área", "Porcentaje"], rows)
    return html


def build_html(snap: dict, root: str) -> str:
    """Return the full report HTML."""
    disclaimer = snap.get("disclaimer") or DEFAULT_DISCLAIMER
    project = escape(str(snap.get("project", {}).get("name", "")))
    body = f"<h1>Informe de viento peatonal · {project}</h1>"
    body += f"<p class='meta'>Generado {escape(str(snap.get('generated_at', '')))} · Ráfaga {escape(str(snap.get('app_version', '')))}</p>"
    site = site_text(snap.get("project", {}))
    if site:
        body += f"<p class='meta'>Ubicación: {site}</p>"
    body += project_section(snap)
    rose = rose_chart((snap.get("wind") or {}).get("rose") or {})
    if rose:
        body += f"<h2>Rosa de vientos</h2><figure><img style='width:9cm' src='{rose}'/></figure>"
    body += parameters_section(snap)
    for study in snap.get("studies", []):
        body += _study(root, study)
    body += comparison_section(snap, root)
    body += f"<h2>Alcance del modelo</h2><p>{escape(MODEL_NOTE)}</p>"
    return f"<html lang='es'><head><meta charset='utf-8'></head><body>{body}</body></html>"


def run_report(raw: dict, settings: Settings) -> str:
    """Write the PDF and return its path relative to DATA_DIR."""
    p = parse_payload(ReportPayload, raw)
    folder = storage.resolve(settings.data_dir, p.output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / f".{p.file_name}.tmp"
    # @font-face only loads through an explicit FontConfiguration.
    fonts = FontConfiguration()
    disclaimer = p.snapshot.get("disclaimer") or DEFAULT_DISCLAIMER
    sheet = CSS(string=css(disclaimer), font_config=fonts)
    HTML(string=build_html(p.snapshot, settings.data_dir)).write_pdf(
        tmp, stylesheets=[sheet], font_config=fonts)
    tmp.replace(folder / p.file_name)
    return f"{p.output_dir.rstrip('/')}/{p.file_name}"
