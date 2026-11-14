"""Analytical tests for the Lawson model (ADR-15)."""

import numpy as np
import pytest

from app.services.comfort.lawson_model import (
    comfort_class, exceedance, gust_factor, sector_of, transfer_factor,
)


def test_transfer_factor_matches_adr_example() -> None:
    assert transfer_factor(1.5, 1.0, 0.03, 60.0) == pytest.approx(0.293, abs=1e-3)


def test_gust_factor_floor_is_one() -> None:
    assert gust_factor(np.array([0.0, 0.25]))[0] == 1.0
    assert gust_factor(np.array([0.5]))[0] == pytest.approx(2.5 / 1.85)


def test_single_sector_closed_form() -> None:
    k = np.full((2, 2), 1.2)
    sector = {"frequency": 0.96, "weibull_k": 2.0, "weibull_c_ms": 5.0, "K": k,
              "G": np.ones((2, 2)), "T": 0.5}
    p = exceedance(4.0, [sector], coverage=1.0)
    expected = 0.96 * np.exp(-(4.0 / (1.2 * 0.5 * 5.0)) ** 2)
    assert np.allclose(p, expected)


def test_partial_coverage_is_renormalised() -> None:
    sector = {"frequency": 0.5, "weibull_k": 2.0, "weibull_c_ms": 5.0, "K": np.ones(1),
              "G": np.ones(1), "T": 1.0}
    assert exceedance(3.0, [sector], 0.5)[0] == pytest.approx(np.exp(-(3 / 5) ** 2))


def test_class_is_first_threshold_within_limit() -> None:
    probs = [np.array([0.2, 0.01, 0.2]), np.array([0.04, 0.0, 0.2]),
             np.array([0.0, 0.0, 0.2]), np.array([0.0, 0.0, 0.2])]
    assert comfort_class(probs, 0.05).tolist() == [1, 0, 4]


@pytest.mark.parametrize("deg,idx", [(0, 0), (11.2, 0), (11.25, 1), (350, 0), (270, 12)])
def test_sector_assignment(deg, idx) -> None:
    assert sector_of(deg, [22.5 * i for i in range(16)]) == idx


def test_hand_computed_single_sector_case() -> None:
    """ERA5 U10 -> U(z_a) over z0 = 1 m, times K, Weibull exceedance, by hand.

    T = ln(2.5)/ln(60) * ln(60/0.03)/ln(10.03/0.03)
      = 0.9162907/4.0943446 * 7.6009025/5.8121387 = 0.2237926 * 1.3077640 = 0.2926699
    I = 0.25 -> G = max(1, 1.75/1.85) = 1.
    K = 2, c = 5, k = 2: scale = 2 * 0.2926699 * 5 = 2.926699 m/s
    P(U > 4) = exp(-(4/2.926699)^2) = exp(-1.867939) = 0.154441 -> not A
    P(U > 6) = exp(-(6/2.926699)^2) = exp(-4.202862) = 0.014953 -> B
    """
    t = transfer_factor(1.5, 1.0, 0.03, 60.0)
    assert t == pytest.approx(0.2926699, rel=1e-6)
    g = gust_factor(np.array([0.25]))
    sector = {"frequency": 1.0, "weibull_k": 2.0, "weibull_c_ms": 5.0, "K": np.array([2.0]),
              "G": g, "T": t}
    p4 = exceedance(4.0, [sector], 1.0)
    p6 = exceedance(6.0, [sector], 1.0)
    assert p4[0] == pytest.approx(0.154441, rel=1e-5)
    assert p6[0] == pytest.approx(0.014953, rel=1e-4)
    assert comfort_class([p4, p6, p6 * 0, p6 * 0], 0.05)[0] == 1  # B


def test_partial_rose_renormalises_by_coverage() -> None:
    """Two simulated sectors of 0.2 + 0.2 with calm 0: P is their weighted mean."""
    t = 0.3
    common = {"weibull_k": 2.0, "weibull_c_ms": 5.0, "G": np.ones(1), "T": t}
    a = common | {"frequency": 0.2, "K": np.array([2.0])}
    b = common | {"frequency": 0.2, "K": np.array([1.0])}
    p = exceedance(4.0, [a, b], coverage=0.4)
    expect = 0.5 * (np.exp(-(4 / 3.0) ** 2) + np.exp(-(4 / 1.5) ** 2))
    assert p[0] == pytest.approx(expect, rel=1e-9)
