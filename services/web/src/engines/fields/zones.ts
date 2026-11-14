import type { Field } from "./field.decode";

/** Cell codes; solids are tracked so areas exclude them. */
export const ZONE = { none: 0, acceleration: 1, stagnation: 2, reduction: 3, solid: 255 } as const;

export interface KThresholds {
  k_accel: number;
  k_stagnation: number;
}

/** Acceleration (K > k_accel) and stagnation (K < k_stagnation) from the K field. */
export function classifyZones(k: Field, t: KThresholds): Uint8Array {
  const out = new Uint8Array(k.data.length);
  for (let i = 0; i < out.length; i += 1) {
    const v = k.data[i];
    out[i] = !Number.isFinite(v) ? ZONE.solid : v > t.k_accel ? ZONE.acceleration : v < t.k_stagnation ? ZONE.stagnation : ZONE.none;
  }
  return out;
}

/** Reduction where ΔK < threshold (threshold is negative, e.g. −0.1). */
export function reductionZones(dk: Field, threshold: number): Uint8Array {
  const out = new Uint8Array(dk.data.length);
  for (let i = 0; i < out.length; i += 1) {
    const v = dk.data[i];
    out[i] = !Number.isFinite(v) ? ZONE.solid : v < threshold ? ZONE.reduction : ZONE.none;
  }
  return out;
}

export interface AreaStat {
  area_m2: number;
  percent: number;
}

export interface ZoneAreaSummary {
  fluidM2: number;
  acceleration: AreaStat;
  stagnation: AreaStat;
  reduction: AreaStat;
}

/** Area per zone in m² and % of the fluid (non-solid) area. */
export function zoneAreas(codes: Uint8Array, dx: number): ZoneAreaSummary {
  const counts = [0, 0, 0, 0];
  let fluid = 0;
  for (const c of codes) {
    if (c === ZONE.solid) continue;
    fluid += 1;
    counts[c] += 1;
  }
  const cell = dx * dx;
  const stat = (n: number): AreaStat => ({ area_m2: n * cell, percent: fluid ? (n / fluid) * 100 : 0 });
  return {
    fluidM2: fluid * cell,
    acceleration: stat(counts[ZONE.acceleration]),
    stagnation: stat(counts[ZONE.stagnation]),
    reduction: stat(counts[ZONE.reduction]),
  };
}

export interface Blob {
  cells: number;
  /** Centroid in cell units (col, row from the south). */
  col: number;
  row: number;
}

function flood(codes: Uint8Array, cols: number, rows: number, start: number, seen: Uint8Array): Blob {
  const stack = [start];
  seen[start] = 1;
  let cells = 0;
  let sc = 0;
  let sr = 0;
  while (stack.length) {
    const i = stack.pop() as number;
    const c = i % cols;
    const r = (i - c) / cols;
    cells += 1;
    sc += c;
    sr += r;
    const next = [c > 0 ? i - 1 : -1, c < cols - 1 ? i + 1 : -1, r > 0 ? i - cols : -1, r < rows - 1 ? i + cols : -1];
    for (const j of next) {
      if (j < 0 || seen[j] || codes[j] !== codes[start]) continue;
      seen[j] = 1;
      stack.push(j);
    }
  }
  // Centroid of cell centres, hence the half-cell offset.
  return { cells, col: sc / cells + 0.5, row: sr / cells + 0.5 };
}

/** Largest 4-connected blob of a zone code: where its label goes. */
export function largestBlob(codes: Uint8Array, cols: number, rows: number, code: number): Blob | null {
  const seen = new Uint8Array(codes.length);
  let best: Blob | null = null;
  for (let i = 0; i < codes.length; i += 1) {
    if (seen[i] || codes[i] !== code) continue;
    const blob = flood(codes, cols, rows, i, seen);
    if (!best || blob.cells > best.cells) best = blob;
  }
  return best;
}
