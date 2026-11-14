"""Plain-Spanish strategy-effect summary (BL-12), the same sentences as the web card.

Keep this module and services/web/src/lib/compare/strategy-summary.ts in step: the golden
strings in tests/services/report/test_report_summary.py and the web test are identical.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

import numpy as np

# |mean dK| below this many percent is "sin cambio relevante".
VERDICT_THRESHOLD_PCT = 3.0

_CLASSES = "ABCDE"
_CLASS_NAMES = {"A": "Sentarse", "B": "Estar de pie", "C": "Pasear", "D": "Caminar con prisa",
                "E": "Incómodo"}
_VERDICT_TEXT = {"improves": "mejora", "worsens": "empeora", "neutral": "sin cambio relevante"}


@dataclass
class ComfortAreas:
    """Lawson class areas (m^2) and the largest gust-safety area of both alternatives."""

    classes_a: dict[str, float]
    classes_b: dict[str, float]
    unsafe_a: float
    unsafe_b: float


@dataclass
class StrategyInput:
    """Everything the summary needs about one alternative against its base."""

    name: str
    base_name: str
    ka: np.ndarray
    kb: np.ndarray
    dk_reduction: float
    reduction_m2: float | None
    accel_a: float
    accel_b: float
    comfort: ComfortAreas | None = None


@dataclass
class StrategySummary:
    """Numbers behind the sentences; no wording."""

    name: str
    base_name: str
    verdict: str
    overall_pct: float
    protected_pct: float | None
    protected_m2: float
    accel: tuple[float, float]
    shift: tuple[str, str, float] | None
    improved_m2: float
    worsened_m2: float
    unsafe: tuple[float, float] | None


def _pct(a: float, b: float, n: int) -> float | None:
    return None if n == 0 or a == 0 else 100.0 * (b - a) / a


def _k_change(ka: np.ndarray, kb: np.ndarray, dk: float) -> tuple[float, float | None]:
    """Return mean K change (percent) overall and over cells losing more than |dk|."""
    both = np.isfinite(ka) & np.isfinite(kb)
    with np.errstate(invalid="ignore"):
        prot = both & ((kb - ka) < dk)
    overall = _pct(float(ka[both].sum()), float(kb[both].sum()), int(both.sum())) or 0.0
    return overall, _pct(float(ka[prot].sum()), float(kb[prot].sum()), int(prot.sum()))


def _class_moves(c: ComfortAreas) -> tuple[float, float, tuple[str, str, float] | None]:
    delta = [c.classes_b.get(k, 0.0) - c.classes_a.get(k, 0.0) for k in _CLASSES]
    cumulative = [sum(delta[: i + 1]) for i in range(len(delta) - 1)]
    improved = max([0.0, *cumulative])
    worsened = max([0.0, *(-v for v in cumulative)])
    lost = [(d, i) for i, d in enumerate(delta) if d < 0]
    gained = [(d, i) for i, d in enumerate(delta) if d > 0]
    shift = None
    if lost and gained:
        # First index wins ties, like the web implementation.
        i_from = min(lost, key=lambda r: (r[0], r[1]))[1]
        i_to = min(gained, key=lambda r: (-r[0], r[1]))[1]
        m2 = min(-delta[i_from], delta[i_to])
        if m2 >= 1:
            shift = (_CLASSES[i_from], _CLASSES[i_to], m2)
    return improved, worsened, shift


def summarize_strategy(i: StrategyInput) -> StrategySummary:
    """Return the verdict and figures of one alternative against its base."""
    overall, protected = _k_change(np.asarray(i.ka, float), np.asarray(i.kb, float), i.dk_reduction)
    prot_m2 = i.reduction_m2 or 0.0
    verdict = ("improves" if overall <= -VERDICT_THRESHOLD_PCT
               else "worsens" if overall >= VERDICT_THRESHOLD_PCT else "neutral")
    improved, worsened, shift = _class_moves(i.comfort) if i.comfort else (0.0, 0.0, None)
    return StrategySummary(
        i.name, i.base_name, verdict, overall, protected if prot_m2 >= 1 else None, prot_m2,
        (i.accel_a, i.accel_b), shift, improved, worsened,
        (i.comfort.unsafe_a, i.comfort.unsafe_b) if i.comfort else None)


def _round(v: float, decimals: int) -> Decimal:
    """Round half away from zero on the shortest decimal form, like Intl.NumberFormat."""
    return Decimal(repr(float(v))).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)


def _area(m2: float) -> str:
    """Return 'N m²' with es-CO thousands dots."""
    return _int(m2) + " m²"


def _int(v: float) -> str:
    return f"{_round(v, 0):,.0f}".replace(",", ".")


def signed_pct(pct: float) -> str:
    """Return a signed one-decimal percent such as '−5,1 %'."""
    sign = "+" if pct > 0 else "−" if pct < 0 else ""
    return f"{sign}{_round(abs(pct), 1):.1f}".replace(".", ",") + " %"


def summary_lines(s: StrategySummary) -> list[str]:
    """Return the summary sentences in the order the web card shows them, verdict last."""
    out: list[str] = []
    if s.protected_pct is not None and s.protected_pct < 0:
        out.append(f"{s.name} reduce el viento un {_int(abs(s.protected_pct))} % en la zona "
                   f"protegida ({_area(s.protected_m2)}).")
    elif s.verdict == "neutral":
        out.append(f"{s.name} casi no cambia el viento en el área analizada.")
    else:
        verb = "reduce" if s.verdict == "improves" else "aumenta"
        out.append(f"{s.name} {verb} el viento un {_int(abs(s.overall_pct))} % en promedio "
                   "en el área analizada.")
    if abs(s.accel[1] - s.accel[0]) >= 1:
        out.append(f"Las zonas de aceleración pasan de {_area(s.accel[0])} a {_area(s.accel[1])}.")
    if s.shift:
        src, dst, m2 = s.shift
        out.append(f"Unos {_area(m2)} pasan de la clase {src} ({_CLASS_NAMES[src]}) a la clase "
                   f"{dst} ({_CLASS_NAMES[dst]}).")
    imp, wor = s.improved_m2 >= 1, s.worsened_m2 >= 1
    if imp and wor:
        out.append(f"Al menos {_area(s.improved_m2)} mejoran de clase y {_area(s.worsened_m2)} empeoran.")
    elif imp:
        out.append(f"Al menos {_area(s.improved_m2)} mejoran de clase.")
    elif wor:
        out.append(f"Al menos {_area(s.worsened_m2)} empeoran de clase.")
    if s.unsafe and max(s.unsafe) >= 1 and abs(s.unsafe[1] - s.unsafe[0]) >= 1:
        out.append(f"El área con ráfagas fuertes pasa de {_area(s.unsafe[0])} a {_area(s.unsafe[1])}.")
    out.append(f"Veredicto: {_VERDICT_TEXT[s.verdict]} frente a {s.base_name}.")
    return out
