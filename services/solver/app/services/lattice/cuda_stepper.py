"""GPU stepper: one fused CuPy RawKernel per step plus an open-boundary pass."""

from pathlib import Path

import numpy as np

from app.services.boundary.profile_nudging import ProfileNudger
from app.services.lattice.lattice_problem import LatticeProblem, initial_populations

# One translation unit: shared constants, the step kernel, the open boundaries.
_SOURCE = "\n".join(
    Path(__file__).with_name(name).read_text(encoding="utf-8")
    for name in ("lbm_lattice.cuh", "lbm_step.cu", "lbm_open.cu")
)
_BLOCK = 256
_MODULES: dict[int, object] = {}


def _module(cp, dim: int):
    """Compile (once per process) the kernel module for a dimension."""
    if dim not in _MODULES:
        _MODULES[dim] = cp.RawModule(code=_SOURCE, options=(f"-DDIM={dim}", "-use_fast_math"))
    return _MODULES[dim]


class GpuStepper:
    """Advance a LatticeProblem on the GPU with the fused kernel."""

    device = "gpu"

    def __init__(self, problem: LatticeProblem) -> None:
        """Upload the problem and allocate the two population buffers."""
        import cupy as cp  # noqa: PLC0415  (only importable on GPU hosts)

        self.cp = self.xp = cp
        self.problem = problem
        mod = _module(cp, problem.dim)
        self.k_step = mod.get_function("lbm_step")
        self.k_open = mod.get_function("open_boundaries")
        self.f = cp.asarray(initial_populations(problem))
        self.g = cp.empty_like(self.f)
        self.mask = cp.asarray(problem.mask.reshape(-1))
        self.pid = cp.asarray(problem.pid.reshape(-1).astype(np.uint16))
        self.ptable = cp.asarray(problem.ptable.astype(np.float32))
        self.sponge = cp.asarray(problem.sponge.astype(np.float32))
        self.inlet = cp.asarray(np.ascontiguousarray(problem.inlet, dtype=np.float32))
        self.lm2 = cp.asarray(problem.length_scale_sq())
        n = problem.nodes
        self.avg_u = cp.zeros((problem.dim, n), dtype=cp.float32)
        self.avg_u2 = cp.zeros(n, dtype=cp.float32)
        self.count = 0
        self.t = 0
        self._dims = self._grid_dims()
        self.nudger = (ProfileNudger(problem.nudge, cp, problem.lattice.c[:, 0])
                       if problem.nudge is not None else None)
        self.fxz = self.nudger.fxz if self.nudger else cp.zeros(1, dtype=cp.float32)

    def _grid_dims(self) -> tuple[int, int, int]:
        """Return (nx, ny, nz) as the kernel expects them."""
        shape = self.problem.shape
        if len(shape) == 2:
            return shape[1], shape[0], 1
        return shape[2], shape[1], shape[0]

    def step(self, n_steps: int, accumulate: bool = False) -> None:
        """Advance n_steps; accumulate the running mean when asked."""
        cp, p = self.cp, self.problem
        nx, ny, nz = self._dims
        blocks = (-(-p.nodes // _BLOCK),)
        row_blocks = (-(-p.rows // _BLOCK),)
        scal = (
            np.int32(nx), np.int32(ny), np.int32(nz), np.int32(p.bottom_wall),
            np.int32(p.ground_bounce), np.float32(p.a_wall), np.float32(p.top_force),
            np.float32(p.tau0), np.float32(p.tau_min), np.float32(p.tau_max),
            np.float32(p.sponge_tau),
        )
        for _ in range(n_steps):
            if accumulate:
                self.count += 1
            inv = np.float32(1.0 / max(self.count, 1))
            self.k_step(blocks, (_BLOCK,), (
                self.f, self.g, self.mask, self.pid, self.ptable, self.sponge, self.lm2,
                self.avg_u, self.avg_u2, *scal, inv, np.int32(accumulate),
                self.fxz, np.int32(self.nudger is not None)))
            k = (self.t // p.inlet_period) % self.inlet.shape[0]
            self.k_open(row_blocks, (_BLOCK,), (
                self.g, self.mask, self.inlet[k], np.int32(nx), np.int32(ny), np.int32(nz)))
            self.f, self.g = self.g, self.f
            self.t += 1
            if self.nudger is not None and self.t % self.nudger.spec.every == 0:
                self.nudger.update(self.f)

    def macroscopic(self):
        """Return density (N,) and velocity (dim, N) as CuPy arrays."""
        cp = self.cp
        c = cp.asarray(self.problem.lattice.c.T.astype(np.float32))
        rho = self.f.sum(axis=0)
        return rho, (c @ self.f) / rho

    def synchronize(self) -> None:
        """Block until queued kernels finished (for timing)."""
        self.cp.cuda.Stream.null.synchronize()

    def close(self) -> None:
        """Free device buffers back to the pool."""
        self.f = self.g = None
        self.cp.get_default_memory_pool().free_all_blocks()
