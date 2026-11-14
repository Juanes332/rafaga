import type { TerrainCategory, WindClimate, WindSector } from "@/types/wind/wind.types";

// Frequencies per 22.5° sector from N clockwise; trade-wind-like, dominant E/ENE.
const FREQ = [0.03, 0.035, 0.06, 0.15, 0.2, 0.11, 0.06, 0.035, 0.025, 0.02, 0.025, 0.03, 0.04, 0.04, 0.035, 0.03];
const P50 = [2.6, 2.9, 3.6, 5.1, 5.6, 4.4, 3.4, 2.7, 2.3, 2.1, 2.4, 2.8, 3.3, 3.5, 3.1, 2.8];

export function eraSectors(): WindSector[] {
  return FREQ.map((frequency, i) => ({
    center_deg: i * 22.5,
    frequency,
    mean_ms: Math.round(P50[i] * 1.06 * 10) / 10,
    p50_ms: P50[i],
    p90_ms: Math.round(P50[i] * 1.75 * 10) / 10,
    max_ms: Math.round(P50[i] * 3.1 * 10) / 10,
    weibull_k: 2.1,
    weibull_c_ms: Math.round(P50[i] * 1.18 * 10) / 10,
  }));
}

export function eraClimate(): WindClimate {
  return {
    source: "era5",
    rose: { sectors: eraSectors(), calm_fraction: 0.05, period_years: 10, hours: 87_648 },
    period_years: 10,
    manual_direction_deg: null,
    manual_u10_ms: null,
    terrain_category: "urban",
    z0_m: 1,
    ustar_ms: 0.48,
    air_density_kg_m3: 1.129,
    fetched_at: "2026-11-12T15:00:00Z",
    from_cache: false,
  };
}

export const TERRAIN: TerrainCategory[] = [
  { key: "open_sea", label_key: "terrain.open_sea", z0_m: 0.0002, default: false },
  { key: "open", label_key: "terrain.open", z0_m: 0.03, default: false },
  { key: "suburban", label_key: "terrain.suburban", z0_m: 0.3, default: false },
  { key: "urban", label_key: "terrain.urban", z0_m: 1, default: true },
  { key: "dense_urban", label_key: "terrain.dense_urban", z0_m: 2, default: false },
];
