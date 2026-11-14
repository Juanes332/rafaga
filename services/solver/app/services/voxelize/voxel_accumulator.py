"""Accumulate primitive coverages into mask + porous table (ADR-13)."""

import numpy as np

from app.services.lattice.lattice_problem import POROUS, PTABLE_COLUMNS, SOLID
from app.services.porous.porous_model import idelchik_zeta

_MAX_IDS = 65535


class VoxelAccumulator:
    """Collect solid coverage, screen and vegetation drag per cell."""

    def __init__(self, shape: tuple[int, ...], solid_threshold: float = 0.5) -> None:
        """Allocate zeroed accumulation fields for a grid shape."""
        self.shape = shape
        self.threshold = solid_threshold
        self.solid = np.zeros(shape, dtype=np.float32)
        self.thin_normal = np.zeros((3,) + shape, dtype=np.float32)
        self.screen = np.zeros(shape, dtype=np.float32)
        self.screen_normal = np.zeros((3,) + shape, dtype=np.float32)
        self.veg = np.zeros(shape, dtype=np.float32)
        self.plate = np.zeros(shape, dtype=np.float32)
        self.plate_normal = np.zeros((3,) + shape, dtype=np.float32)

    def add_solid(self, window: tuple[slice, ...], cov: np.ndarray, normal) -> None:
        """Add a solid's coverage; remember its normal where it dominates."""
        region = self.solid[window]
        dominant = cov > region
        for k in range(3):
            self.thin_normal[(k,) + window][dominant] = normal[k]
        self.solid[window] = np.minimum(region + cov, 1.0)

    def add_plate(self, window: tuple[slice, ...], cov_plane: np.ndarray, normal) -> None:
        """Add a solid plate thinner than the cell by its in-plane coverage.

        A 0.3 m canopy fills 15 % of a 2 m cell but blocks 100 % of the
        flow through its plane: its open fraction is 1 - cov_plane, not
        1 - volume coverage (which made fins and canopies transparent).
        """
        region = self.plate[window]
        dominant = cov_plane > region
        for k in range(3):
            self.plate_normal[(k,) + window][dominant] = normal[k]
        self.plate[window] = np.minimum(region + cov_plane, 1.0)

    def add_screen(self, window: tuple[slice, ...], a: np.ndarray, normal) -> None:
        """Add a screen's drag; the stronger screen keeps its normal."""
        region = self.screen[window]
        stronger = a > region
        for k in range(3):
            self.screen_normal[(k,) + window][stronger] = normal[k]
        self.screen[window] = np.maximum(region, a)

    def add_vegetation(self, window: tuple[slice, ...], a: np.ndarray) -> None:
        """Add vegetation drag (additive)."""
        self.veg[window] += a

    def finish(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return mask (uint8), porous id (uint16) and table (float32)."""
        solid = self.solid >= self.threshold
        thin = (self.solid > 0) & ~solid
        beta = np.clip(1.0 - self.solid, 0.05, 1.0)
        a_thin = np.where(thin, 0.5 * idelchik_zeta(beta), 0.0).astype(np.float32)
        plate = (self.plate > 0) & ~solid
        beta_plate = np.clip(1.0 - self.plate, 0.05, 1.0)
        a_plate = np.where(plate, 0.5 * idelchik_zeta(beta_plate), 0.0).astype(np.float32)
        use_plate = a_plate > a_thin
        a_thin = np.where(use_plate, a_plate, a_thin)
        thin_normal = np.where(use_plate[None], self.plate_normal, self.thin_normal)
        use_thin = a_thin > self.screen
        a_scr = np.where(use_thin, a_thin, self.screen)
        normal = np.where(use_thin[None], thin_normal, self.screen_normal)
        rows = np.stack([a_scr, normal[0], normal[1], normal[2], self.veg], axis=-1)
        porous = ~solid & ((a_scr > 0) | (self.veg > 0))
        mask = np.where(solid, SOLID, np.where(porous, POROUS, 0)).astype(np.uint8)
        return (mask,) + _table(rows, porous)


def _table(rows: np.ndarray, porous: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Deduplicate porous rows into a lookup table, id 0 = no porosity."""
    pid = np.zeros(porous.shape, dtype=np.uint16)
    picked = rows[porous].astype(np.float32)
    if picked.size == 0:
        return pid, np.zeros((1, PTABLE_COLUMNS), dtype=np.float32)
    digits = 6
    while True:
        rounded = np.round(picked, digits)
        uniq, inverse = np.unique(rounded, axis=0, return_inverse=True)
        if len(uniq) <= _MAX_IDS or digits == 1:
            break
        digits -= 1
    pid[porous] = (inverse.reshape(-1) + 1).astype(np.uint16)
    table = np.vstack([np.zeros((1, PTABLE_COLUMNS)), uniq]).astype(np.float32)
    return pid, table
