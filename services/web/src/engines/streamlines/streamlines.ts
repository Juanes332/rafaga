/** Velocity components on the output grid (cell units, row 0 = south). NaN = solid. */
export interface VectorField {
  cols: number;
  rows: number;
  u: Float32Array;
  v: Float32Array;
}

interface TraceOptions {
  step: number;
  maxSteps: number;
}

function bilinear(a: Float32Array, cols: number, rows: number, x: number, y: number): number {
  const gx = Math.max(0, Math.min(cols - 1, x - 0.5));
  const gy = Math.max(0, Math.min(rows - 1, y - 0.5));
  const c0 = Math.floor(gx);
  const r0 = Math.floor(gy);
  const c1 = Math.min(c0 + 1, cols - 1);
  const r1 = Math.min(r0 + 1, rows - 1);
  const tx = gx - c0;
  const ty = gy - r0;
  const top = a[r0 * cols + c0] * (1 - tx) + a[r0 * cols + c1] * tx;
  const bottom = a[r1 * cols + c0] * (1 - tx) + a[r1 * cols + c1] * tx;
  return top * (1 - ty) + bottom * ty;
}

/** Unit direction at (x, y); null outside, inside solids or where the air is still. */
function direction(f: VectorField, x: number, y: number, sign: number): [number, number] | null {
  if (x < 0 || y < 0 || x > f.cols || y > f.rows) return null;
  const u = bilinear(f.u, f.cols, f.rows, x, y);
  const v = bilinear(f.v, f.cols, f.rows, x, y);
  const m = Math.hypot(u, v);
  if (!Number.isFinite(m) || m < 1e-6) return null;
  return [(sign * u) / m, (sign * v) / m];
}

/** Midpoint (RK2) streamline from (x0, y0); flat [x0, y0, x1, y1, …] in cell units. */
export function traceStreamline(f: VectorField, x0: number, y0: number, o: TraceOptions, sign = 1): number[] {
  const pts = [x0, y0];
  let x = x0;
  let y = y0;
  for (let i = 0; i < o.maxSteps; i += 1) {
    const d1 = direction(f, x, y, sign);
    if (!d1) break;
    const d2 = direction(f, x + (d1[0] * o.step) / 2, y + (d1[1] * o.step) / 2, sign);
    if (!d2) break;
    x += d2[0] * o.step;
    y += d2[1] * o.step;
    pts.push(x, y);
  }
  return pts;
}

/** Seeds on a square lattice, `spacing` cells apart, offset by half a spacing. */
export function seedGrid(cols: number, rows: number, spacing: number): Array<[number, number]> {
  const seeds: Array<[number, number]> = [];
  for (let y = spacing / 2; y < rows; y += spacing) for (let x = spacing / 2; x < cols; x += spacing) seeds.push([x, y]);
  return seeds;
}

/** Static streamlines for reduced motion / no WebGL2: one line per seed, traced both ways. */
export function computeStreamlines(f: VectorField, spacing: number, maxSteps = 400): number[][] {
  const opts = { step: 0.6, maxSteps };
  const lines: number[][] = [];
  for (const [x, y] of seedGrid(f.cols, f.rows, spacing)) {
    const back = traceStreamline(f, x, y, opts, -1);
    const fwd = traceStreamline(f, x, y, opts, 1);
    const joined: number[] = [];
    for (let i = back.length - 2; i >= 2; i -= 2) joined.push(back[i], back[i + 1]);
    joined.push(...fwd);
    if (joined.length >= 8) lines.push(joined);
  }
  return lines;
}
