/** Pure parts of the particle engine (design-system §7); the GPU side mirrors these formulas. */

interface CountInput {
  width: number;
  dpr: number;
  meanFrameMs: number | null;
  /** Canvas area in CSS px²; density is capped at ~1 particle per 60 px². */
  area?: number;
}

export function particleCount({ width, dpr, meanFrameMs, area }: CountInput): number {
  const base = width < 768 ? 8192 : dpr >= 2 && meanFrameMs !== null && meanFrameMs < 10 ? 32768 : 16384;
  if (area === undefined) return base;
  return Math.max(1024, Math.min(base, Math.round(area / 60 / 128) * 128));
}

export const PX_PER_K = 0.6;
export const MAX_PX = 3;

/** Screen displacement per frame: K × 0.6 px × zoom, capped at 3 px. */
export function particleStep(k: number, zoom: number): number {
  return Math.min(k * PX_PER_K * zoom, MAX_PX);
}

export interface VelocityData {
  /** RG interleaved: unit direction × K (so speed reads relative to U_ref). */
  velocity: Float32Array;
  /** RG interleaved fluid cell centres, for respawning outside solids. */
  fluid: Float32Array;
  fluidCount: number;
  meanU: number;
  meanV: number;
}

export function buildVelocityData(K: Float32Array, ux: Float32Array, uy: Float32Array, cols: number, rows: number): VelocityData {
  const velocity = new Float32Array(cols * rows * 2);
  const fluid = new Float32Array(cols * rows * 2);
  let n = 0;
  let su = 0;
  let sv = 0;
  for (let i = 0; i < cols * rows; i += 1) {
    const k = K[i];
    const m = Math.hypot(ux[i], uy[i]);
    if (!Number.isFinite(k) || !Number.isFinite(m)) continue;
    const s = m > 1e-9 ? k / m : 0;
    velocity[i * 2] = ux[i] * s;
    velocity[i * 2 + 1] = uy[i] * s;
    su += velocity[i * 2];
    sv += velocity[i * 2 + 1];
    fluid[n * 2] = (i % cols) + 0.5;
    fluid[n * 2 + 1] = Math.floor(i / cols) + 0.5;
    n += 1;
  }
  return { velocity, fluid: fluid.slice(0, n * 2), fluidCount: n, meanU: n ? su / n : 0, meanV: n ? sv / n : 0 };
}

/** Segment [x0, y0, x1, y1] on the boundary the mean flow comes from. */
export function upwindEdge(meanU: number, meanV: number, cols: number, rows: number): [number, number, number, number] {
  if (Math.abs(meanU) >= Math.abs(meanV)) {
    const x = meanU < 0 ? cols - 0.5 : 0.5;
    return [x, 0, x, rows];
  }
  const y = meanV < 0 ? rows - 0.5 : 0.5;
  return [0, y, cols, y];
}

/** Rolling 30-frame budget: halve particles when the mean exceeds 20 ms (then start over). */
export class FrameBudget {
  private samples: number[] = [];

  push(ms: number): void {
    this.samples.push(ms);
    if (this.samples.length > 30) this.samples.shift();
  }

  mean(): number | null {
    return this.samples.length ? this.samples.reduce((a, b) => a + b, 0) / this.samples.length : null;
  }

  shouldDegrade(): boolean {
    const m = this.mean();
    if (this.samples.length < 30 || m === null || m <= 20) return false;
    this.samples = [];
    return true;
  }
}

export interface ViewInput {
  cols: number;
  rows: number;
  width: number;
  height: number;
  /** Pixels per cell. */
  ppc: number;
  /** Top-left of the grid in canvas pixels. */
  ox: number;
  oy: number;
}

/** [sx, sy, tx, ty]: clip = cell × s + t, with row 0 (south) at the bottom. */
export function viewTransform(v: ViewInput): [number, number, number, number] {
  const sx = (2 * v.ppc) / v.width;
  const sy = (2 * v.ppc) / v.height;
  return [sx, sy, (2 * v.ox) / v.width - 1, 1 - (2 * (v.oy + v.rows * v.ppc)) / v.height];
}
