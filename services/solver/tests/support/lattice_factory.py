"""Build small synthetic LatticeProblems for tests."""

import numpy as np

from app.services.lattice.lattice_problem import LatticeProblem


def make_problem(shape: tuple[int, ...], seed: int = 0, bottom_wall: bool = True,
                 with_obstacles: bool = True, u_in: float = 0.05,
                 abl: bool = False, nudge: bool = False) -> LatticeProblem:
    """Return a problem with a block, porous cells and a sponge."""
    rng = np.random.default_rng(seed)
    dim = len(shape)
    nx = shape[-1]
    mask = np.zeros(shape, dtype=np.uint8)
    pid = np.zeros(shape, dtype=np.uint16)
    if with_obstacles:
        block = tuple(slice(s // 3, s // 3 + max(2, s // 5)) for s in shape[:-1])
        mask[block + (slice(nx // 3, nx // 3 + 3),)] = 1
        porous = tuple(slice(0, max(1, s // 2)) for s in shape[:-1]) + (slice(nx // 2, nx // 2 + 2),)
        mask[porous] = 2
        pid[porous] = rng.integers(1, 3, size=pid[porous].shape)
    ptable = np.zeros((3, 5), dtype=np.float32)
    ptable[1, :] = [4.0, 1.0, 0.0, 0.0, 0.0]
    ptable[2, :] = [0.0, 0.0, 0.0, 0.0, 0.3]
    sponge = np.clip((np.arange(nx) - 0.8 * nx) / (0.2 * nx), 0, 1).astype(np.float32)
    rows = int(np.prod(shape[:-1]))
    inlet = np.zeros((2, dim, rows), dtype=np.float32)
    inlet[:, 0, :] = u_in
    inlet[1] += rng.normal(0, 0.001, size=(dim, rows)).astype(np.float32)
    problem = LatticeProblem(
        shape=shape, mask=mask, pid=pid, ptable=ptable, sponge=sponge, inlet=inlet,
        tau0=0.5005, smagorinsky_cs=0.17, bottom_wall=bottom_wall, a_wall=0.02,
        inlet_period=3,
    )
    if abl:
        problem.ground_slip = True
        problem.top_force = 2e-5
        problem.mixing_length = rng.uniform(0.17, 3.0, size=shape).astype(np.float32)
    if nudge:
        from app.services.boundary.profile_nudging import nudge_spec

        target = np.full(shape[0], 1.2 * u_in, dtype=np.float32)
        problem.nudge = nudge_spec(mask, sponge, target, ft_steps=20)
    return problem
