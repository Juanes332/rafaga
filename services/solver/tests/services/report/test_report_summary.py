"""Strategy-effect summary shared with the web card (BL-12). Golden strings equal the web test."""

import numpy as np
import pytest

from app.services.report.report_summary import (
    VERDICT_THRESHOLD_PCT,
    ComfortAreas,
    StrategyInput,
    summarize_strategy,
    summary_lines,
)

GOLDEN = StrategyInput(
    name="Celosía 40 %", base_name="Caso base",
    ka=np.ones(8), kb=np.array([0.6, 0.6, 1, 1, 1, 1, 1, 1.0]), dk_reduction=-0.1,
    reduction_m2=200.0, accel_a=800.0, accel_b=500.0,
    comfort=ComfortAreas(classes_a={"A": 100, "B": 200, "C": 1000, "D": 50, "E": 0},
                         classes_b={"A": 100, "B": 520, "C": 680, "D": 50, "E": 0},
                         unsafe_a=40.0, unsafe_b=10.0),
)
SENTENCES = [
    "Celosía 40 % reduce el viento un 40 % en la zona protegida (200 m²).",
    "Las zonas de aceleración pasan de 800 m² a 500 m².",
    "Unos 320 m² pasan de la clase C (Pasear) a la clase B (Estar de pie).",
    "Al menos 320 m² mejoran de clase.",
    "El área con ráfagas fuertes pasa de 40 m² a 10 m².",
    "Veredicto: mejora frente a Caso base.",
]


def _with(**kw) -> StrategyInput:
    return StrategyInput(**{**GOLDEN.__dict__, **kw})


def test_golden_sentences_match_the_web_card() -> None:
    assert summary_lines(summarize_strategy(GOLDEN)) == SENTENCES


def test_verdict_threshold_is_three_percent() -> None:
    assert VERDICT_THRESHOLD_PCT == 3
    base = np.ones(4)
    verdict = lambda v: summarize_strategy(_with(ka=base, kb=base * v, dk_reduction=-0.5)).verdict  # noqa: E731
    assert (verdict(0.96), verdict(1.04), verdict(0.98), verdict(1.02)) == (
        "improves", "worsens", "neutral", "neutral")


def test_protected_zone_and_non_fluid_cells() -> None:
    s = summarize_strategy(_with(ka=np.ones(4), kb=np.array([0.5, 0.5, 1, 1.0])))
    assert s.protected_pct == pytest.approx(-50.0)
    assert s.overall_pct == pytest.approx(-25.0)
    s = summarize_strategy(_with(ka=np.array([1, np.nan, 1.0]), kb=np.array([0.9, 5, np.nan]),
                                 dk_reduction=-0.5, reduction_m2=0.0))
    assert s.overall_pct == pytest.approx(-10.0) and s.protected_pct is None


def test_no_change_is_said_plainly_and_without_comfort_has_no_lawson_lines() -> None:
    s = summarize_strategy(_with(ka=np.ones(2), kb=np.array([1.01, 0.99]), comfort=None, reduction_m2=0.0,
                                 accel_b=800.0))
    text = " ".join(summary_lines(s))
    assert "casi no cambia el viento" in text and "Veredicto: sin cambio relevante" in text
    assert "clase" not in text


def test_areas_use_thousands_dots() -> None:
    s = summarize_strategy(_with(reduction_m2=1250.0))
    assert "(1.250 m²)" in summary_lines(s)[0]


def test_rounding_matches_the_web_half_away_from_zero() -> None:
    """Intl.NumberFormat rounds half away from zero; Python's format() rounds half to even."""
    from app.services.report.report_summary import _area, _int, signed_pct

    assert (_int(2.5), _int(12.5), _int(1.005 * 1000)) == ("3", "13", "1.005")
    assert _area(1500.5) == "1.501 m²"
    assert (signed_pct(0.25), signed_pct(-0.25), signed_pct(1.05)) == ("+0,3 %", "−0,3 %", "+1,1 %")
