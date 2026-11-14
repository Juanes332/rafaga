"""Regularized inlet/outlet columns on NumPy (twin of `open_boundaries`)."""

import numpy as np

from app.services.lattice.numpy_collision import CollisionTables


def _column(
    f: np.ndarray, src: np.ndarray, tables: CollisionTables,
    rho_set: float | None, u_set: np.ndarray | None,
) -> np.ndarray:
    """Return eq(rho, u) + regularized neq copied from the source column."""
    g = f[:, src]
    rho = g.sum(axis=0)
    v = (tables.c.T @ g) / rho
    cu = tables.c @ v
    vsq = (v * v).sum(axis=0)
    feq = tables.w * rho * (1 + 3 * cu + np.float32(4.5) * cu * cu - np.float32(1.5) * vsq)
    pi = tables.pair_c @ (g - feq)
    r = rho if rho_set is None else np.float32(rho_set)
    w_u = v if u_set is None else u_set
    cw = tables.c @ w_u
    wsq = (w_u * w_u).sum(axis=0)
    eq = tables.w * r * (1 + 3 * cw + np.float32(4.5) * cw * cw - np.float32(1.5) * wsq)
    return eq + np.float32(4.5) * tables.w * (tables.qmat @ pi)


def apply_open_boundaries(
    f: np.ndarray, tables: CollisionTables, inlet_nodes: np.ndarray,
    outlet_nodes: np.ndarray, u_in: np.ndarray,
) -> None:
    """Overwrite inlet and outlet columns of f (Q, N) in place.

    inlet_nodes/outlet_nodes are flat indices of fluid nodes at x=0 and
    x=nx-1; u_in is (dim, len(inlet_nodes)).
    """
    if inlet_nodes.size:
        f[:, inlet_nodes] = _column(f, inlet_nodes + 1, tables, 1.0, u_in)
    if outlet_nodes.size:
        f[:, outlet_nodes] = _column(f, outlet_nodes - 1, tables, 1.0, None)
