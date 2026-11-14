"""ENU <-> simulation-frame transforms (job-contract.md section 3.1)."""

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class WindFrame:
    """Rotation taking ENU points to the wind-aligned simulation frame."""

    d: tuple[float, float]  # flow direction (sim x) in ENU
    n: tuple[float, float]  # sim y in ENU

    @classmethod
    def from_wind(cls, wind_from_deg: float) -> "WindFrame":
        """Return the frame for a meteorological 'from' direction."""
        phi = math.radians(wind_from_deg)
        return cls((-math.sin(phi), -math.cos(phi)), (math.cos(phi), -math.sin(phi)))

    @classmethod
    def identity(cls) -> "WindFrame":
        """Return the north-up frame (x east, y north)."""
        return cls((1.0, 0.0), (0.0, 1.0))

    def affine(self) -> list[float]:
        """Return shapely affine parameters [a, b, d, e, xoff, yoff]."""
        return [self.d[0], self.d[1], self.n[0], self.n[1], 0.0, 0.0]

    def to_sim(self, x, y) -> tuple[np.ndarray, np.ndarray]:
        """Return sim-frame coordinates of ENU points."""
        x, y = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
        return x * self.d[0] + y * self.d[1], x * self.n[0] + y * self.n[1]

    def to_enu_vector(self, vx, vy) -> tuple[np.ndarray, np.ndarray]:
        """Return ENU components of a sim-frame vector field."""
        return vx * self.d[0] + vy * self.n[0], vx * self.d[1] + vy * self.n[1]
