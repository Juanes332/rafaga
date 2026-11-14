"""Synthetic turbulent inflow for the 3D LES (digital filter + Lund).

A white-noise box (frames x z x y) is Gaussian-filtered (Klein et al.
2003), normalised per level and mapped by Lund's transform onto a
neutral-ABL Reynolds stress tensor: sigma_u = 2.5 u*, sigma_v = 0.75
sigma_u, sigma_w = 0.5 sigma_u, <u'w'> = -u*^2, with sigma_u capped at
INFLOW_IU_CAP U(z). The shifted log law gives U -> 0 at the ground, so
an uncapped 2.5 u* would mean Iu > 1 at pedestrian height. Frames are
one cell of frozen turbulence apart (Taylor), FRAME_STEPS lattice steps
at u_lat = 0.05, and the bank wraps seamlessly in time. Built on the
CPU so NumPy and CuPy runs see the same inflow.
"""

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import gaussian_filter

INFLOW_IU_CAP = 0.22
FRAME_STEPS = 20
MIN_FRAMES, MAX_FRAMES = 64, 512
MAX_BANK_BYTES = 64 * 1024 * 1024
_RATIO_V, _RATIO_W, _SIGMA_U_USTAR = 0.75, 0.5, 2.5


@dataclass(frozen=True)
class InflowSpec:
    """Inputs of one inflow bank, all in lattice units."""

    profile: np.ndarray  # (nz,) mean streamwise inlet velocity
    ny: int
    ustar: float
    length_cells: float  # streamwise integral length of the filter
    seed: int
    frames: int | None = None  # None: as many as max_bytes allows
    max_bytes: int = MAX_BANK_BYTES


def target_stresses(profile: np.ndarray, ustar: float):
    """Return (sigma_u, sigma_v, sigma_w, <u'w'>) per level."""
    u = np.asarray(profile, dtype=np.float64)
    su = np.minimum(_SIGMA_U_USTAR * ustar, INFLOW_IU_CAP * u)
    sv, sw = _RATIO_V * su, _RATIO_W * su
    # Realizability: |<u'w'>| < sigma_u sigma_w where the cap bites.
    uw = -np.minimum(ustar * ustar, 0.9 * su * sw)
    return su, sv, sw, uw


def _frame_count(spec: InflowSpec) -> int:
    """Return the number of frames that fit the byte budget."""
    if spec.frames is not None:
        return spec.frames
    frame_bytes = 3 * spec.profile.size * spec.ny * 4
    return int(np.clip(spec.max_bytes // frame_bytes, MIN_FRAMES, MAX_FRAMES))


def _unit_field(rng: np.random.Generator, shape: tuple[int, int, int], sigma) -> np.ndarray:
    """Return filtered noise with zero mean and unit variance per level."""
    r = gaussian_filter(rng.standard_normal(shape), sigma=sigma,
                        mode=("wrap", "reflect", "reflect"))
    r -= r.mean(axis=(0, 2), keepdims=True)
    r /= np.maximum(r.std(axis=(0, 2), keepdims=True), 1e-12)
    return r


def _decorrelated(r: np.ndarray, ref: np.ndarray) -> np.ndarray:
    """Return r with its sample correlation to ref removed per level.

    A finite bank keeps a few percent of chance correlation, which would
    bias <u'w'> away from the Lund target.
    """
    proj = (r * ref).mean(axis=(0, 2), keepdims=True)
    out = r - proj * ref
    return out / np.maximum(out.std(axis=(0, 2), keepdims=True), 1e-12)


def turbulent_inlet_bank(spec: InflowSpec) -> np.ndarray:
    """Return the (frames, 3, nz*ny) float32 inlet velocity bank."""
    nz, ny = spec.profile.size, spec.ny
    frames = _frame_count(spec)
    lx = max(spec.length_cells, 2.0)
    # Gaussian sigma ~ L/2; cross-stream scales half the streamwise one.
    sigma = (lx / 2.0, min(lx / 4.0, nz / 4.0), min(lx / 4.0, ny / 4.0))
    rng = np.random.default_rng(spec.seed)
    r1, r2, r3 = (_unit_field(rng, (frames, nz, ny), sigma) for _ in range(3))
    r3 = _decorrelated(r3, r1)
    su, sv, sw, uw = (s[None, :, None] for s in target_stresses(spec.profile, spec.ustar))
    a31 = uw / su
    a33 = np.sqrt(np.maximum(sw * sw - a31 * a31, 0.0))
    bank = np.empty((frames, 3, nz * ny), dtype=np.float32)
    mean = np.asarray(spec.profile, dtype=np.float64)[None, :, None]
    bank[:, 0] = (mean + su * r1).reshape(frames, -1)
    bank[:, 1] = (sv * r2).reshape(frames, -1)
    bank[:, 2] = (a31 * r1 + a33 * r3).reshape(frames, -1)
    return bank
