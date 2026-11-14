"""A fixed obstacle-in-channel lattice used for benchmarks (versioned)."""

import numpy as np

from app.services.boundary.log_profile import sponge_ramp
from app.services.lattice.lattice_problem import LatticeProblem

BENCH_CASE_VERSION = "1"


def synthetic_problem(shape: tuple[int, ...], u_lat: float = 0.05) -> LatticeProblem:
    """Return a channel with one block a third of the way downstream."""
    dim, nx = len(shape), shape[-1]
    mask = np.zeros(shape, dtype=np.uint8)
    block = tuple(slice(s // 2 - max(1, s // 10), s // 2 + max(1, s // 10)) for s in shape[:-1])
    if dim == 3:
        block = (slice(0, shape[0] // 3),) + block[1:]
    mask[block + (slice(nx // 3, nx // 3 + max(2, nx // 20)),)] = 1
    rows = int(np.prod(shape[:-1]))
    inlet = np.zeros((1, dim, rows), dtype=np.float32)
    inlet[0, 0] = u_lat
    return LatticeProblem(
        shape=shape, mask=mask, pid=np.zeros(shape, dtype=np.uint16),
        ptable=np.zeros((1, 5), dtype=np.float32), sponge=sponge_ramp(nx, 0.1), inlet=inlet,
        tau0=0.50015, smagorinsky_cs=0.17, bottom_wall=dim == 3, a_wall=0.05,
    )
