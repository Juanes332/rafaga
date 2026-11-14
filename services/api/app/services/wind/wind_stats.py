"""Wind rose statistics from hourly speed and direction (pure numpy)."""

import math

import numpy as np

CALM_MS = 0.5
SECTORS = 16
SECTOR_WIDTH = 360.0 / SECTORS


def weibull_fit(speeds: np.ndarray) -> tuple[float, float]:
    """Return Weibull (k, c) by maximum likelihood (Newton iteration).

    Degenerate samples fall back to k=2 with c from the mean.
    """
    u = speeds[speeds > 0]
    if u.size < 2 or float(np.std(u)) < 1e-9:
        mean = float(u.mean()) if u.size else 0.0
        return 2.0, mean / math.gamma(1.5)
    k = (float(np.std(u)) / float(np.mean(u))) ** -1.086
    logs = np.log(u)
    for _ in range(50):
        uk = u**k
        f = (uk * logs).sum() / uk.sum() - 1.0 / k - logs.mean()
        df = ((uk * logs**2).sum() * uk.sum() - ((uk * logs).sum()) ** 2) / uk.sum() ** 2 + 1.0 / k**2
        step = f / df
        k = max(k - step, 0.05)
        if abs(step) < 1e-8:
            break
    return float(k), float((np.mean(u**k)) ** (1.0 / k))


def _sector_stats(index: int, speeds: np.ndarray, total: int) -> dict:
    """Build one WindSector dict from the speeds falling in it."""
    center = index * SECTOR_WIDTH
    if speeds.size == 0:
        return {"center_deg": center, "frequency": 0.0, "mean_ms": 0.0, "p50_ms": 0.0,
                "p90_ms": 0.0, "max_ms": 0.0, "weibull_k": 2.0, "weibull_c_ms": 0.0}
    k, c = weibull_fit(speeds)
    return {"center_deg": center, "frequency": speeds.size / total,
            "mean_ms": float(speeds.mean()), "p50_ms": float(np.percentile(speeds, 50)),
            "p90_ms": float(np.percentile(speeds, 90)), "max_ms": float(speeds.max()),
            "weibull_k": k, "weibull_c_ms": c}


def build_rose(speed: list[float], direction: list[float], period_years: int) -> dict:
    """Return the WindRose dict; frequencies plus calm sum to one.

    Hours with missing values are dropped. Direction is the
    meteorological 'from' bearing; sector i covers
    [22.5 i - 11.25, 22.5 i + 11.25).
    """
    spd, dr = np.asarray(speed, dtype=float), np.asarray(direction, dtype=float)
    ok = ~(np.isnan(spd) | np.isnan(dr))
    spd, dr = spd[ok], dr[ok]
    total = int(spd.size)
    if total == 0:
        raise ValueError("no valid hours")
    calm = spd < CALM_MS
    index = np.floor(((dr % 360.0) + SECTOR_WIDTH / 2) / SECTOR_WIDTH).astype(int) % SECTORS
    sectors = [_sector_stats(i, spd[~calm & (index == i)], total) for i in range(SECTORS)]
    return {"sectors": sectors, "calm_fraction": float(calm.sum() / total),
            "period_years": period_years, "hours": total}
