"""Forcing + regularized BGK/Smagorinsky collision on NumPy (CPU twin).

Mirrors the arithmetic of lbm_step.cu so that CPU and GPU agree to
float32 rounding; every step here has its line in the kernel.
"""

from dataclasses import dataclass

import numpy as np

from app.services.lattice.lattice_constants import Lattice

_SQRT2_18 = np.float32(25.455844)


@dataclass(frozen=True)
class CollisionTables:
    """Float32 lattice tables precomputed once per run."""

    c: np.ndarray  # (Q, dim)
    w: np.ndarray  # (Q, 1)
    pair_c: np.ndarray  # (P, Q) c_a c_b for the P stress components
    pair_weight: np.ndarray  # (P,) 1 for diagonal, 2 for off-diagonal
    qmat: np.ndarray  # (Q, P) (c_a c_b - delta/3) * pair weight


def build_tables(lat: Lattice) -> CollisionTables:
    """Return the float32 tables for one lattice."""
    dim = lat.dim
    pairs = [(a, a) for a in range(dim)]
    pairs += [(a, b) for a in range(dim) for b in range(a + 1, dim)]
    c = lat.c.astype(np.float32)
    pair_c = np.stack([c[:, a] * c[:, b] for a, b in pairs])
    weight = np.array([1.0 if a == b else 2.0 for a, b in pairs], dtype=np.float32)
    delta = np.array([1.0 if a == b else 0.0 for a, b in pairs], dtype=np.float32)
    qmat = (pair_c - delta[:, None] / 3).T * weight
    w = lat.w.astype(np.float32)[:, None]
    return CollisionTables(c, w, pair_c, weight, qmat.astype(np.float32))


@dataclass
class NodeForcing:
    """Per-chunk forcing inputs."""

    porous_idx: np.ndarray  # local indices of porous nodes
    porous_rows: np.ndarray  # (k, 5) table rows for those nodes
    wall_idx: np.ndarray  # local indices of first-layer ground nodes
    a_wall: float
    top_idx: np.ndarray | None = None  # local indices of the top layer
    top_force: float = 0.0
    body_fx: np.ndarray | None = None  # per-node streamwise nudging force


def drag_factor(a, speed):
    """Return |u|/|u*| solving |u| + (a/2)|u|^2 = |u*| exactly (ADR-13)."""
    return np.float32(2) / (1 + np.sqrt(1 + np.float32(2) * a * speed))


def apply_forcing(u: np.ndarray, forcing: NodeForcing, dim: int) -> None:
    """Apply vegetation, screen and wall drag implicitly, in place."""
    idx, rows = forcing.porous_idx, forcing.porous_rows
    if idx.size:
        v = u[:, idx]
        a_veg = rows[:, 4]
        v *= drag_factor(a_veg, np.sqrt((v * v).sum(0)))
        normal = rows[:, 1 : 1 + dim].T
        a_scr = rows[:, 0]
        un = (v * normal).sum(0)
        d = un * drag_factor(a_scr, np.abs(un)) - un
        v += d * normal
        u[:, idx] = v
    if forcing.wall_idx.size:
        h = u[: dim - 1, forcing.wall_idx]
        mag = np.sqrt((h * h).sum(0))
        u[: dim - 1, forcing.wall_idx] = h * drag_factor(np.float32(forcing.a_wall), mag)


def _apply_streamwise_forces(u: np.ndarray, forcing: NodeForcing, rho: np.ndarray) -> None:
    """Add half of the top shear and nudging forces to u_x (Guo), in place."""
    if forcing.top_force and forcing.top_idx is not None and forcing.top_idx.size:
        idx = forcing.top_idx
        u[0, idx] += np.float32(0.5) * np.float32(forcing.top_force) / rho[idx]
    if forcing.body_fx is not None:
        u[0] += np.float32(0.5) * forcing.body_fx / rho


def relaxation_time(
    pi: np.ndarray, pair_weight: np.ndarray, rho: np.ndarray, params: dict
) -> np.ndarray:
    """Return tau_eff from Hou et al. Smagorinsky, clamped (ADR-14)."""
    pnorm = np.sqrt((pair_weight[:, None] * pi * pi).sum(0))
    tau0 = np.float32(params["tau0"])
    tau = np.float32(0.5) * (
        tau0 + np.sqrt(tau0 * tau0 + _SQRT2_18 * np.float32(params["cs2"]) * pnorm / rho)
    )
    return np.clip(tau, np.float32(params["tau_min"]), np.float32(params["tau_max"]))


def _equilibrium(tables: CollisionTables, rho: np.ndarray, u: np.ndarray):
    """Return (f_eq, c.u) with few temporaries."""
    cu = tables.c @ u
    feq = cu * np.float32(4.5)
    feq += np.float32(3)
    feq *= cu
    feq += 1 - np.float32(1.5) * (u * u).sum(axis=0)
    feq *= tables.w * rho
    return feq, cu


def collide(
    f: np.ndarray, tables: CollisionTables, forcing: NodeForcing,
    sponge: np.ndarray, params: dict,
) -> tuple[np.ndarray, np.ndarray]:
    """Return post-collision populations and the forced velocity."""
    dim = tables.c.shape[1]
    rho = f.sum(axis=0)
    s = (tables.c.T @ f) / rho
    u = s.copy()
    apply_forcing(u, forcing, dim)
    _apply_streamwise_forces(u, forcing, rho)
    force = np.float32(2) * rho * (u - s)
    feq, cu = _equilibrium(tables, rho, u)
    pi = tables.pair_c @ (f - feq)
    tau = relaxation_time(pi, tables.pair_weight, rho, params)
    tau += (np.float32(params["sponge_tau"]) - tau) * sponge
    c_f = tables.c @ force
    src = _guo_source(tables, cu, c_f, u, force, tau)
    # Regularization drops the first moment of f - feq (= -F/2); add its
    # relaxed part back so the net momentum gain is exactly F (kernel twin).
    neq = tables.qmat @ pi
    neq *= np.float32(4.5)
    neq -= np.float32(1.5) * c_f
    neq *= tables.w * (1 - 1 / tau)
    feq += neq
    feq += src
    return feq, u


def _guo_source(tables, cu, c_f, u, force, tau):
    """Return (1 - 1/2tau) w (cF (3 + 9 cu) - 3 u.F), reusing cu in place."""
    cu *= np.float32(9)
    cu += np.float32(3)
    cu *= c_f
    cu -= np.float32(3) * (u * force).sum(axis=0)
    cu *= tables.w * (1 - np.float32(0.5) / tau)
    return cu
