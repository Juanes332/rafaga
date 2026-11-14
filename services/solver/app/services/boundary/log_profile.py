"""Shifted log-law profile (ADR-20) and inlet/wall-function helpers (ADR-12)."""

import numpy as np

KAPPA = 0.41


def friction_velocity(u10_ms: float, z0_m: float, kappa: float = KAPPA) -> float:
    """Return u* = kappa U10 / ln((10 + z0)/z0)."""
    return kappa * u10_ms / np.log((10.0 + z0_m) / z0_m)


def log_speed(z_m, ustar_ms: float, z0_m: float, kappa: float = KAPPA):
    """Return U(z) = (u*/kappa) ln((z + z0)/z0); defined for every z >= 0."""
    return (ustar_ms / kappa) * np.log((np.asarray(z_m) + z0_m) / z0_m)


def profile_ratio(z_m, z_ref_m: float, z0_m: float):
    """Return U(z)/U(z_ref), independent of u*."""
    return np.log((np.asarray(z_m) + z0_m) / z0_m) / np.log((z_ref_m + z0_m) / z0_m)


def lattice_inlet_profile(nz: int, dx_m: float, z0_m: float, u_lat: float) -> np.ndarray:
    """Return u_lat(z) at cell centres, scaled so the domain top equals u_lat."""
    z = (np.arange(nz) + 0.5) * dx_m
    return (u_lat * profile_ratio(z, nz * dx_m, z0_m)).astype(np.float32)


def wall_drag_coefficient(dx_m: float, z0_m: float, kappa: float = KAPPA) -> float:
    """Return a in F = -rho a |U| U for the first fluid layer (z1 = dx/2)."""
    return float((kappa / np.log((0.5 * dx_m + z0_m) / z0_m)) ** 2)


def sponge_ramp(nx: int, fraction: float) -> np.ndarray:
    """Return the outlet sponge weight, 0 upstream rising to 1 at x = nx-1."""
    start = int(np.floor(nx * (1.0 - fraction)))
    x = np.arange(nx, dtype=np.float64)
    width = max(nx - 1 - start, 1)
    return np.clip((x - start) / width, 0.0, 1.0).astype(np.float32)


def perturbation_bank(
    base: np.ndarray, amplitude: float, seed: int, count: int = 32
) -> np.ndarray:
    """Return (count, dim, rows) inlet fields with seeded relative noise.

    Generated on the CPU so NumPy and CuPy runs see identical inflow.
    """
    if amplitude <= 0:
        return base[None].astype(np.float32)
    rng = np.random.default_rng(seed)
    speed = np.abs(base[0])[None, None, :]
    noise = rng.uniform(-1.0, 1.0, size=(count,) + base.shape) * amplitude * speed
    return (base[None] + noise).astype(np.float32)
