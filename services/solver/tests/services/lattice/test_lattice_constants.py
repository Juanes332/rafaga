"""Tests for the lattice velocity sets."""

import numpy as np
import pytest

from app.services.lattice.lattice_constants import D2Q9, D3Q19


@pytest.mark.parametrize("lat", [D2Q9, D3Q19])
def test_weights_sum_to_one_and_isotropy_holds(lat) -> None:
    assert lat.w.sum() == pytest.approx(1.0)
    second = np.einsum("q,qa,qb->ab", lat.w, lat.c, lat.c)
    assert np.allclose(second, np.eye(lat.dim) / 3)


@pytest.mark.parametrize("lat", [D2Q9, D3Q19])
def test_opposite_and_mirror_tables_are_consistent(lat) -> None:
    assert (lat.c[lat.opposite] == -lat.c).all()
    for d in range(lat.dim):
        flipped = lat.c[lat.mirror[d]]
        assert (flipped[:, d] == -lat.c[:, d]).all()


def test_sets_have_expected_sizes() -> None:
    assert (D2Q9.q, D3Q19.q) == (9, 19)


def _cuda_table(block: str, name: str) -> list[int]:
    import re

    body = re.search(rf"{name}\[Q\] = \{{([^}}]*)\}}", block).group(1)
    return [int(v) for v in body.replace("\n", " ").split(",") if v.strip()]


@pytest.mark.parametrize("lat,dim", [(D2Q9, 2), (D3Q19, 3)])
def test_cuda_tables_match_python_tables(lat, dim) -> None:
    from pathlib import Path

    src = (Path(__file__).resolve().parents[3] / "app/services/lattice/lbm_lattice.cuh").read_text()
    two, three = src.split("#else")
    block = two if dim == 2 else three
    for axis, name in enumerate(("CX", "CY", "CZ")[:dim]):
        assert _cuda_table(block, name) == lat.c[:, axis].tolist()
    assert _cuda_table(block, "OPP") == lat.opposite.tolist()
    assert _cuda_table(block, "MY") == lat.mirror[1].tolist()
    if dim == 3:
        assert _cuda_table(block, "MZ") == lat.mirror[2].tolist()
