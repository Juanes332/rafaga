"""Report section comparing every alternative with the baseline (US-13, US-14)."""

import json
from html import escape

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from app.models.scene.scene_schemas import Scene
from app.services.postprocess.delta_service import delta_figure
from app.services.render import map_style as st
from app.services.render.map_decorations import add_facade_elements
from app.services.render.cardinal import wind_from_text
from app.services.render.map_figure import draw_scalar
from app.services.render.render_service import load_field
from app.services.report.report_badge import add_report_wind_badge
from app.services.report.report_compass import add_report_compass
from app.services.report.report_charts import png_data_uri
from app.services.report.report_html import num, table
from app.services.report.report_summary import (
    ComfortAreas,
    StrategyInput,
    summarize_strategy,
    summary_lines,
)
from app.services.storage import output_dir_service as storage

_ZONES = (("acceleration", "Aceleración"), ("stagnation", "Estancamiento"), ("reduction", "Reducción"))


def zone_rows(base: np.ndarray, alt: np.ndarray, dx: float, th: dict) -> dict[str, dict]:
    """Return zone areas (m^2) of base and alternative; reduction only for the alternative."""
    cell = dx * dx

    def areas(k: np.ndarray, delta: np.ndarray | None) -> dict:
        fluid = np.isfinite(k)
        return {
            "acceleration": float((fluid & (k > th["k_accel"])).sum() * cell),
            "stagnation": float((fluid & (k < th["k_stagnation"])).sum() * cell),
            "reduction": None if delta is None
            else float((np.isfinite(delta) & (delta < th["dk_reduction"])).sum() * cell),
            "fluid": float(fluid.sum() * cell),
        }

    with np.errstate(invalid="ignore"):
        return {"base": areas(base, None), "alt": areas(alt, alt - base)}


def rank_alternatives(saved: dict[str, list[float]]) -> list[tuple[str, float]]:
    """Return (name, acceleration area saved in m^2 summed over directions), best first."""
    return sorted(((name, float(sum(v))) for name, v in saved.items()), key=lambda r: -r[1])


def load_scene(root: str, result_dir: str) -> Scene | None:
    """Return the scene stored beside a result, if the result has one."""
    path = storage.resolve(root, result_dir) / "scene.json"
    if not path.exists():
        return None
    return Scene.model_validate(json.loads(path.read_text(encoding="utf-8")))


def _extent(root: str, result_dir: str) -> tuple[float, float, float, float]:
    """Return the plot extent of a result."""
    bundle = np.load(storage.resolve(root, result_dir) / "fields.npz")
    return tuple(float(v) for v in bundle["extent"])

# Side-by-side panels of a site wider than 2:1 would be too short for a legible badge (BL-07).
WIDE_STACK_RATIO = 0.5


def _side_by_side_figure(panels: list[tuple[str, np.ndarray, Scene | None]], extent,
                         wind: float) -> Figure:
    """Return base | alternative K maps sharing one colour scale."""
    vmax = max(float(np.nanmax(k)) for _, k, _ in panels)
    x0, x1, y0, y1 = extent
    ratio = (y1 - y0) / max(x1 - x0, 1e-9)
    stacked = ratio < WIDE_STACK_RATIO  # very wide sites: panels one above the other
    if stacked:
        fig = Figure(figsize=(7.0, len(panels) * (6.0 * ratio + 0.9) + 0.6), layout="constrained")
    else:
        height = 3.2 * ratio + 1.2
        fig = Figure(figsize=(9.0, min(max(height, 3.0), 7.0)), layout="constrained")
    FigureCanvasAgg(fig)
    axes = fig.subplots(len(panels), 1, sharex=True) if stacked else fig.subplots(1, len(panels), sharey=True)
    for ax, (title, k, scene) in zip(np.atleast_1d(axes), panels):
        ax.set_aspect("equal")
        image = draw_scalar(fig, ax, k, extent, st.K_CMAP, "K", 0.0, vmax, smooth=scene is not None,
                            colorbar=False)
        add_facade_elements(ax, scene)
        add_report_wind_badge(ax, wind)
        add_report_compass(ax)
        ax.set_title(title, fontsize=9)
        ax.xaxis.set_major_formatter(st.comma_formatter(0))
        ax.yaxis.set_major_formatter(st.comma_formatter(0))
    bar = fig.colorbar(image, ax=list(np.atleast_1d(axes)), shrink=0.8)
    bar.set_label("K = U / U_ref(z_a)")
    bar.ax.yaxis.set_major_formatter(st.comma_formatter(2))
    return fig


def _side_by_side(panels: list[tuple[str, np.ndarray, Scene | None]], extent, wind: float) -> str:
    """Return the side-by-side figure as a data URI."""
    return png_data_uri(_side_by_side_figure(panels, extent, wind), dpi=130)


def _pct(area: float | None, fluid: float) -> str:
    """Return 'area m² (pct %)' with decimal commas."""
    if area is None:
        return "—"
    return f"{num(area, 0)} m² ({num(100 * area / max(fluid, 1e-9), 1)} %)"


def _direction_block(root: str, base: dict, alts: list[tuple[dict, dict]], th: dict,
                     saved: dict[str, list[float]], reduction: dict[str, float],
                     base_accel: list[float], samples: dict[str, list[dict]]) -> str:
    """Return figures and the zone table of one direction."""
    wind = float(base["wind_from_deg"])
    k_base = load_field(root, base["result_dir"], "K")
    extent = _extent(root, base["result_dir"])
    dx = (extent[1] - extent[0]) / k_base.shape[1]
    base_scene = load_scene(root, base["result_dir"])
    html = f"<h3>Viento {wind_from_text(wind)}</h3>"
    rows, first = [], True
    for study, res in alts:
        name = str(study.get("alternative_name", ""))
        k_alt = load_field(root, res["result_dir"], "K")
        if k_alt.shape != k_base.shape:
            continue
        scene = load_scene(root, res["result_dir"])
        uri = _side_by_side([("Caso base", k_base, base_scene), (name, k_alt, scene)], extent, wind)
        caption = f"K: caso base frente a {escape(name)}"
        html += f"<figure><img src='{uri}'/><figcaption>{caption}</figcaption></figure>"
        fig, delta_ax = delta_figure(k_alt - k_base, extent, scene, wind, th["dk_reduction"], width_in=6.2,
                              title=f"ΔK · {name} − caso base")
        add_report_compass(delta_ax)
        html += f"<figure><img src='{png_data_uri(fig, dpi=130)}'/></figure>"
        z = zone_rows(k_base, k_alt, dx, th)
        if first:
            base_accel[0] += z["base"]["acceleration"]
            rows.append(["Caso base"] + [_pct(z["base"][k], z["base"]["fluid"]) for k, _ in _ZONES])
            first = False
        rows.append([escape(name)] + [_pct(z["alt"][k], z["alt"]["fluid"]) for k, _ in _ZONES])
        saved.setdefault(name, []).append(z["base"]["acceleration"] - z["alt"]["acceleration"])
        reduction[name] = reduction.get(name, 0.0) + (z["alt"]["reduction"] or 0.0)
        samples.setdefault(name, []).append({
            "ka": k_base, "kb": k_alt, "reduction": z["alt"]["reduction"] or 0.0,
            "accel_a": z["base"]["acceleration"], "accel_b": z["alt"]["acceleration"]})
    if rows:
        html += table(["Alternativa"] + [label for _, label in _ZONES], rows)
    return html


_NEGLIGIBLE = 0.05  # acceleration-area changes under 5 % of the base area are noise-level


def _comfort_areas(base: dict, alt: dict) -> ComfortAreas | None:
    """Return both studies' Lawson areas, or None unless both have them."""
    a, b = base.get("comfort_areas") or {}, alt.get("comfort_areas") or {}
    if not a.get("class_areas") or not b.get("class_areas"):
        return None

    def classes(c: dict) -> dict[str, float]:
        return {str(r["class"]): float(r["area_m2"]) for r in c["class_areas"]}

    def unsafe(c: dict) -> float:
        return max([0.0, *(float(r.get("area_m2") or 0.0) for r in c.get("safety_areas") or [])])

    return ComfortAreas(classes(a), classes(b), unsafe(a), unsafe(b))


def strategy_effects(base: dict, others: list[dict], samples: dict[str, list[dict]],
                     th: dict) -> list[tuple[str, list[str]]]:
    """Return (alternative name, summary sentences) as the web card words them (BL-12).

    Several directions are pooled: K cells are concatenated and areas averaged per direction.
    """
    out = []
    for study in others:
        name = str(study.get("alternative_name", ""))
        rows = samples.get(name)
        if not rows:
            continue
        n = len(rows)
        summary = summarize_strategy(StrategyInput(
            name=name, base_name=str(base.get("alternative_name", "Caso base")),
            ka=np.concatenate([r["ka"].ravel() for r in rows]),
            kb=np.concatenate([r["kb"].ravel() for r in rows]),
            dk_reduction=th["dk_reduction"], reduction_m2=sum(r["reduction"] for r in rows) / n,
            accel_a=sum(r["accel_a"] for r in rows) / n, accel_b=sum(r["accel_b"] for r in rows) / n,
            comfort=_comfort_areas(base, study)))
        out.append((name, summary_lines(summary)))
    return out


def conclusion(ranked: list[tuple[str, float]], base_accel: float, reduction: dict[str, float],
               n_dirs: int, kind: str | None,
               effects: list[tuple[str, list[str]]] | None = None) -> str:
    """Return a short plain-Spanish conclusion ranking the alternatives."""
    if not ranked:
        return ""
    dirs = "la dirección simulada" if n_dirs == 1 else f"las {n_dirs} direcciones simuladas"
    small = _NEGLIGIBLE * max(base_accel, 1e-9)
    best, gain = ranked[0]
    if gain > small:
        text = (f"{escape(best)} es la alternativa que más reduce el área de aceleración "
                f"(K &gt; umbral): {num(gain, 0)} m² menos que el caso base, sumando {dirs}.")
        rest = ranked[1:]
    else:
        text = (f"Ninguna alternativa cambia de forma apreciable el área de aceleración en {dirs} "
                f"(diferencias menores del {num(100 * _NEGLIGIBLE, 0)} % de los "
                f"{num(base_accel, 0)} m² del caso base).")
        rest = []
    for name, value in rest:
        verb = "apenas cambia" if abs(value) <= small else ("la reduce en" if value > 0 else "la aumenta en")
        text += f" {escape(name)} {verb}" + ("." if verb == "apenas cambia" else f" {num(abs(value), 0)} m².")
    if reduction:
        lead, area = max(reduction.items(), key=lambda kv: kv[1])
        if area > 0:
            text += (f" La mayor zona de reducción local (ΔK &lt; umbral) es la de {escape(lead)}: "
                     f"{num(area, 0)} m², aunque el viento que desvía puede acelerarse en otro punto.")
    if kind == "plan2d":
        text += (" En planta 2D no se representan marquesinas ni efectos de bajada de viento por "
                 "la fachada; esas estrategias deben evaluarse en 3D.")
    html = f"<p><strong>Conclusión.</strong> {text}</p>"
    if effects:
        html += "<h3>Efecto de cada estrategia</h3>"
        for name, lines in effects:
            items = "".join(f"<li>{escape(line)}</li>" for line in lines)
            html += f"<h4>{escape(name)}</h4><ul>{items}</ul>"
    return html


def comparison_section(snap: dict, root: str) -> str:
    """Return the comparison HTML, or '' without a baseline and an alternative."""
    studies = snap.get("studies") or []
    base_id = snap.get("baseline_study_id")
    base = next((s for s in studies if str(s.get("study_id")) == str(base_id)), None)
    others = [s for s in studies if s is not base and s.get("kind") == (base or {}).get("kind")]
    if base is None or not others:
        return ""
    th = {"k_accel": 1.2, "k_stagnation": 0.3, "dk_reduction": -0.1} | (snap.get("thresholds") or {})
    html = ("<h2 style='page-break-before: always'>Comparación con el caso base</h2>"
            "<p class='meta'>Mapas lado a lado con la misma escala de K, mapa ΔK (reducción "
            f"ΔK &lt; {num(th['dk_reduction'])} contorneada) y áreas por zona.</p>")
    saved: dict[str, list[float]] = {}
    reduction: dict[str, float] = {}
    base_accel = [0.0]
    samples: dict[str, list[dict]] = {}
    n_dirs = 0
    for res in base.get("results", []):
        wind = float(res["wind_from_deg"])
        alts = [(s, r) for s in others for r in s.get("results", [])
                if abs(float(r["wind_from_deg"]) - wind) < 1e-6]
        if alts:
            n_dirs += 1
            html += _direction_block(root, res, alts, th, saved, reduction, base_accel, samples)
    return html + conclusion(rank_alternatives(saved), base_accel[0], reduction, n_dirs,
                             base.get("kind"), strategy_effects(base, others, samples, th))



