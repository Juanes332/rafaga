"""Pull-streaming wall rules as precomputed fix-up links (CPU path).

The rules are the ones of lbm_step.cu `pull()`: x is periodic (the
open columns are overwritten afterwards), lateral/top faces reflect
specularly, the ground and solid nodes bounce back half-way.
"""

import numpy as np

from app.services.lattice.lattice_constants import Lattice
from app.services.lattice.lattice_problem import SOLID


def _coords(shape: tuple[int, ...]) -> list[np.ndarray]:
    """Return per-axis integer coordinates (x, y[, z]) of every node."""
    grids = np.indices(shape).reshape(len(shape), -1)
    return [g for g in grids[::-1]]


def _apply_rows(
    lat: Lattice, q: int, coords: list[np.ndarray], shape: tuple[int, ...],
    bottom_wall: bool,
) -> tuple[list[np.ndarray], np.ndarray, np.ndarray]:
    """Return source coordinates, source population and bounce flags."""
    dim = lat.dim
    src = [coords[d] - lat.c[q, d] for d in range(dim)]
    src[0] %= shape[-1]
    qq = np.full(src[0].shape, q)
    bb = np.zeros(src[0].shape, dtype=bool)
    for d in range(1, dim):
        size = shape[dim - 1 - d]
        low, high = src[d] < 0, src[d] >= size
        is_bottom_axis = d == dim - 1
        ground = bottom_wall and is_bottom_axis
        reflect = high | (low & (not ground))
        if bottom_wall and is_bottom_axis:
            bb |= low
        src[d] = np.where(reflect | low, coords[d], src[d])
        qq = np.where(reflect, lat.mirror[d][qq], qq)
    return src, qq, bb


def build_links(
    lat: Lattice, shape: tuple[int, ...], mask: np.ndarray, bottom_wall: bool
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Return per-q (dest node, flat source) pairs that differ from a roll."""
    coords = _coords(shape)
    n_nodes = int(np.prod(shape))
    node = np.arange(n_nodes)
    flat_mask = mask.reshape(-1)
    links = []
    for q in range(lat.q):
        src, qq, bb = _apply_rows(lat, q, coords, shape, bottom_wall)
        sn = np.zeros(n_nodes, dtype=np.int64)
        for d in reversed(range(lat.dim)):
            sn = sn * shape[lat.dim - 1 - d] + src[d]
        bb |= flat_mask[sn] == SOLID
        fix = (bb | (qq != q)) & (flat_mask != SOLID)
        source = np.where(bb, lat.opposite[q] * n_nodes + node, qq * n_nodes + sn)
        links.append((node[fix], source[fix]))
    return links
