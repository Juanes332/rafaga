"""CPU stepper: NumPy pull-stream + collision split in thread slabs."""

import os
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from threadpoolctl import threadpool_limits

from app.services.boundary.profile_nudging import ProfileNudger
from app.services.lattice.lattice_problem import (
    SOLID,
    LatticeProblem,
    initial_populations,
)
from app.services.lattice.numpy_collision import NodeForcing, build_tables, collide
from app.services.lattice.open_boundaries import apply_open_boundaries
from app.services.lattice.stream_links import build_links

_MIN_SLAB = 16384


class _Slab:
    """Contiguous node range with its local forcing inputs."""

    def __init__(self, problem: LatticeProblem, start: int, stop: int) -> None:
        """Precompute the slab's porous, wall, solid and sponge data."""
        self.sl = slice(start, stop)
        pid = problem.pid.reshape(-1)[start:stop]
        porous = np.flatnonzero(pid > 0)
        node = np.arange(start, stop)
        wall = np.zeros(0, dtype=np.int64)
        layer = problem.nx * (problem.rows // problem.shape[0])
        if problem.bottom_wall:
            wall = np.flatnonzero(node < layer)
        top = np.flatnonzero(node >= problem.nodes - layer)
        self.forcing = NodeForcing(porous, problem.ptable[pid[porous]], wall, problem.a_wall,
                                   top, problem.top_force)
        self.cs2 = problem.length_scale_sq()[start:stop]
        self.solid = np.flatnonzero(problem.mask.reshape(-1)[start:stop] == SOLID)
        self.sponge = problem.sponge[node % problem.nx].astype(np.float32)
        # (z * nx + x) of every node: index into the nudging force lines.
        self.line = (node // layer) * problem.nx + node % problem.nx


class CpuStepper:
    """Advance a LatticeProblem with NumPy; same algorithm as the GPU path."""

    device = "cpu"

    def __init__(self, problem: LatticeProblem, threads: int | None = None) -> None:
        """Allocate populations and precompute links, slabs and boundaries."""
        # Slab threads already use every core; BLAS threads on top of
        # them oversubscribe the CPU and halve throughput.
        threadpool_limits(1, user_api="blas")
        self.problem = problem
        self.xp = np
        self.tables = build_tables(problem.lattice)
        self.links = build_links(problem.lattice, problem.shape, problem.mask,
                                 problem.ground_bounce)
        self.f = initial_populations(problem)
        n, dim = problem.nodes, problem.dim
        self.avg_u = np.zeros((dim, n), dtype=np.float32)
        self.avg_u2 = np.zeros(n, dtype=np.float32)
        self.count = 0
        self.t = 0
        # Hyper-threads add contention, not bandwidth: one thread per core.
        self.threads = threads or max(1, min(8, (os.cpu_count() or 2) // 2))
        size = max(_MIN_SLAB, -(-n // self.threads))
        self.slabs = [_Slab(problem, s, min(n, s + size)) for s in range(0, n, size)]
        self.pool = ThreadPoolExecutor(self.threads)
        self.nudger = (ProfileNudger(problem.nudge, np, problem.lattice.c[:, 0])
                       if problem.nudge is not None else None)
        self.params = {
            "tau0": problem.tau0,
            "tau_min": problem.tau_min, "tau_max": problem.tau_max,
            "sponge_tau": problem.sponge_tau,
        }
        self._init_boundaries()

    def _init_boundaries(self) -> None:
        """Locate fluid nodes of the inlet and outlet columns."""
        p = self.problem
        rows = np.arange(p.rows) * p.nx
        fluid = p.mask.reshape(-1) != SOLID
        self.inlet_rows = np.flatnonzero(fluid[rows])
        self.inlet_nodes = rows[self.inlet_rows]
        self.outlet_nodes = rows[fluid[rows + p.nx - 1]] + p.nx - 1
        self.wvec = self.tables.w[:, 0]

    def _stream_q(self, q: int, src_flat: np.ndarray, out: np.ndarray) -> None:
        """Pull population q by a periodic roll, then patch wall links."""
        p = self.problem
        c = p.lattice.c[q]
        shifts = tuple(int(c[d]) for d in reversed(range(p.dim)))
        rolled = np.roll(self.f[q].reshape(p.shape), shifts, axis=tuple(range(p.dim)))
        out[q] = rolled.reshape(-1)
        dest, src = self.links[q]
        out[q, dest] = src_flat[src]

    def _collide_slab(self, slab: _Slab, pulled: np.ndarray, out: np.ndarray, acc: bool) -> None:
        """Collide one slab and update its running averages."""
        params = self.params | {"cs2": slab.cs2}
        if self.nudger is not None:
            slab.forcing.body_fx = self.nudger.fxz[slab.line]
        post, u = collide(pulled[:, slab.sl], self.tables, slab.forcing, slab.sponge, params)
        post[:, slab.solid] = self.wvec[:, None]
        out[:, slab.sl] = post
        if acc:
            u[:, slab.solid] = 0  # The GPU kernel never averages solid nodes.
            inv = np.float32(1.0 / self.count)
            avg = self.avg_u[:, slab.sl]
            avg += (u - avg) * inv
            avg2 = self.avg_u2[slab.sl]
            avg2 += ((u * u).sum(0) - avg2) * inv

    def step(self, n_steps: int, accumulate: bool = False) -> None:
        """Advance n_steps; accumulate the running mean when asked."""
        q_count = self.problem.lattice.q
        for _ in range(n_steps):
            pulled = np.empty_like(self.f)
            flat = self.f.reshape(-1)
            list(self.pool.map(lambda q: self._stream_q(q, flat, pulled), range(q_count)))
            if accumulate:
                self.count += 1
            out = np.empty_like(self.f)
            list(self.pool.map(lambda s: self._collide_slab(s, pulled, out, accumulate), self.slabs))
            apply_open_boundaries(out, self.tables, self.inlet_nodes, self.outlet_nodes, self._inlet())
            self.f = out
            self.t += 1
            if self.nudger is not None and self.t % self.nudger.spec.every == 0:
                self.nudger.update(self.f)

    def _inlet(self) -> np.ndarray:
        """Return the inlet velocity of the current step for fluid rows."""
        bank = self.problem.inlet
        k = (self.t // self.problem.inlet_period) % bank.shape[0]
        return bank[k][:, self.inlet_rows]

    def macroscopic(self) -> tuple[np.ndarray, np.ndarray]:
        """Return density (N,) and velocity (dim, N) of the current state."""
        rho = self.f.sum(axis=0)
        return rho, (self.tables.c.T @ self.f) / rho

    def close(self) -> None:
        """Release the worker threads."""
        self.pool.shutdown(wait=False)
