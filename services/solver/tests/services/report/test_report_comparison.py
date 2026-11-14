"""Report comparison section: side by side, dK, zone areas, ranking (US-13/14)."""

import copy
import re
from pathlib import Path

import numpy as np
import pytest
from pypdf import PdfReader

from app.configs.config import Settings
from app.services.report.report_comparison import rank_alternatives, zone_rows
from app.services.report.report_service import run_report
from app.services.simulation.heavy_job_service import run_heavy_job
from tests.support.contracts import example
from tests.support.payload_factory import plan_payload

TH = {"k_accel": 1.2, "k_stagnation": 0.3, "dk_reduction": -0.1}


def test_zone_rows_count_cells_against_thresholds() -> None:
    base = np.array([[1.3, 0.2], [1.0, np.nan]])
    alt = np.array([[1.1, 0.2], [1.3, np.nan]])
    rows = zone_rows(base, alt, dx=2.0, th=TH)
    assert rows["base"] == {"acceleration": 4.0, "stagnation": 4.0, "reduction": None, "fluid": 12.0}
    assert rows["alt"] == {"acceleration": 4.0, "stagnation": 4.0, "reduction": 4.0, "fluid": 12.0}


def test_ranking_orders_by_acceleration_area_saved() -> None:
    ranked = rank_alternatives({"Celosía": [100.0, -20.0], "Aletas": [10.0, 5.0]})
    assert [r[0] for r in ranked] == ["Celosía", "Aletas"]
    assert ranked[0][1] == pytest.approx(80.0)


@pytest.fixture(scope="module")
def alt_dir(result_store) -> str:
    raw = plan_payload(dx=6.0, wind_from=270.0, device="cpu")
    raw["scene"]["porous"][0]["z_max"] = 24.0
    raw["output_dir"] = "results/p/alt/j"
    manifest = run_heavy_job(raw, "alt", Settings(data_dir=result_store.settings.data_dir,
                                                  rafaga_device="cpu"), lambda *_: False)
    return manifest["dir"]


def test_report_has_comparison_section_with_ranking(result_store, alt_dir) -> None:
    raw = copy.deepcopy(example("job.report.example"))
    snap = raw["snapshot"]
    base = copy.deepcopy(snap["studies"][0])
    base.update({"study_id": "base", "alternative_name": "Caso base", "comfort_dir": None,
                 "results": [{"result_dir": result_store.dirs[270.0], "wind_from_deg": 270.0,
                              "convergence": {"converged": True}}]})
    alt = copy.deepcopy(base)
    alt.update({"study_id": "alt", "alternative_name": "Celosía 40 %",
                "results": [{"result_dir": alt_dir, "wind_from_deg": 270.0,
                             "convergence": {"converged": True}}]})
    snap.update({"studies": [base, alt], "baseline_study_id": "base", "thresholds": TH})
    rel = run_report(raw, result_store.settings)
    text = " ".join(p.extract_text() for p in PdfReader(Path(result_store.settings.data_dir) / rel).pages)
    assert "Comparación con el caso base" in text
    assert "Viento desde O · 270°" in text
    for word in ("Aceleración", "Estancamiento", "Reducción", "Conclusión"):
        assert word in text
    assert "Celosía 40 %" in text
    flat = " ".join(text.split())
    assert "Efecto de cada estrategia" in flat
    assert "Veredicto:" in flat and "frente a Caso base" in flat
    assert re.search(r"Celosía 40 % (reduce|aumenta|casi no cambia) el viento", flat)
    # BL-12: model-confidence note merged with the closing scope section.
    assert ("Ráfaga sirve para comparar alternativas y detectar zonas incómodas en etapas de diseño. "
            "No reemplaza un ensayo en túnel de viento para proyectos críticos.") in flat


def test_conclusion_calls_small_changes_negligible_and_names_the_reduction_leader() -> None:
    from app.services.report.report_comparison import conclusion

    text = conclusion([("Celosía", 12.0), ("Aletas", -12.0)], base_accel=772.0,
                      reduction={"Celosía": 12.0, "Aletas": 400.0}, n_dirs=1, kind="volume3d")
    assert "Ninguna alternativa cambia de forma apreciable" in text and "400 m²" in text
    # The leader of local reduction is never also called unchanged.
    assert "apenas cambia" not in text
    strong = conclusion([("Celosía", 300.0)], base_accel=772.0, reduction={"Celosía": 500.0},
                        n_dirs=1, kind="volume3d")
    assert "más reduce el área de aceleración" in strong


def test_conclusion_appends_the_strategy_summaries() -> None:
    from app.services.report.report_comparison import conclusion

    text = conclusion([("Celosía", 300.0)], base_accel=772.0, reduction={"Celosía": 500.0}, n_dirs=1,
                      kind="volume3d", effects=[("Celosía", ["Celosía reduce el viento un 40 %.", "Veredicto: mejora frente a Caso base."])])
    assert "Efecto de cada estrategia" in text and "Veredicto: mejora frente a Caso base." in text
