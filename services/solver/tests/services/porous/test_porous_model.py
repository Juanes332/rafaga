"""Tests for porous coefficients (ADR-13 table)."""

import pytest

from app.services.porous.porous_model import (
    idelchik_zeta, screen_coefficient, vegetation_coefficient,
)


@pytest.mark.parametrize("beta,zeta", [(0.05, 1074.66), (0.2, 51.29), (0.4, 8.23),
                                       (0.6, 1.99), (0.95, 0.048)])
def test_idelchik_matches_adr_table(beta, zeta) -> None:
    assert float(idelchik_zeta(beta)) == pytest.approx(zeta, rel=0.01)


def test_screen_coefficient_spreads_over_thickness() -> None:
    assert screen_coefficient(8.0, 2.0) == pytest.approx(2.0)
    assert screen_coefficient(8.0, 0.1) == pytest.approx(4.0)


def test_vegetation_coefficient_uses_lattice_lad() -> None:
    assert vegetation_coefficient(0.2, 1.0, 2.0) == pytest.approx(0.4)
