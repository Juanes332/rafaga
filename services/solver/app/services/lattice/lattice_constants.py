"""D2Q9 and D3Q19 velocity sets shared by the NumPy and CUDA paths.

The index order here is the order hard-coded in lbm_lattice.cuh; the two
must never diverge (tests compare them).
"""

from dataclasses import dataclass

import numpy as np

_D2Q9_C = [(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (-1, 1), (-1, -1), (1, -1)]
_D2Q9_W = [4 / 9] + [1 / 9] * 4 + [1 / 36] * 4

_D3Q19_C = [
    (0, 0, 0),
    (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1),
    (1, 1, 0), (-1, -1, 0), (1, -1, 0), (-1, 1, 0),
    (1, 0, 1), (-1, 0, -1), (1, 0, -1), (-1, 0, 1),
    (0, 1, 1), (0, -1, -1), (0, 1, -1), (0, -1, 1),
]
_D3Q19_W = [1 / 3] + [1 / 18] * 6 + [1 / 36] * 12


@dataclass(frozen=True)
class Lattice:
    """One discrete velocity set with its derived index tables."""

    name: str
    dim: int
    c: np.ndarray  # (Q, dim) int
    w: np.ndarray  # (Q,) float64
    opposite: np.ndarray  # (Q,) index of -c
    mirror: np.ndarray  # (dim, Q) index with component d negated

    @property
    def q(self) -> int:
        """Return the number of discrete velocities."""
        return int(self.c.shape[0])


def _index_of(c: np.ndarray, target: np.ndarray) -> int:
    """Return the row of c equal to target."""
    return int(np.flatnonzero((c == target).all(axis=1))[0])


def _build(name: str, vectors: list[tuple[int, ...]], weights: list[float]) -> Lattice:
    """Assemble a Lattice and its opposite/mirror tables."""
    c = np.array(vectors, dtype=np.int64)
    dim = c.shape[1]
    opposite = np.array([_index_of(c, -v) for v in c])
    mirror = np.zeros((dim, len(c)), dtype=np.int64)
    for d in range(dim):
        flip = np.ones(dim, dtype=np.int64)
        flip[d] = -1
        mirror[d] = [_index_of(c, v * flip) for v in c]
    return Lattice(name, dim, c, np.array(weights), opposite, mirror)


D2Q9 = _build("D2Q9", _D2Q9_C, _D2Q9_W)
D3Q19 = _build("D3Q19", _D3Q19_C, _D3Q19_W)


def lattice_for_dim(dim: int) -> Lattice:
    """Return D2Q9 for 2D and D3Q19 for 3D."""
    return D2Q9 if dim == 2 else D3Q19
