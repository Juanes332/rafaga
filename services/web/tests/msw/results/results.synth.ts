import { GRID, U_REF } from "./results.ids";

interface Box {
  x0: number;
  x1: number;
  y0: number;
  y1: number;
}

// Same blocks as tests/msw/geometry sampleBuildings(); wind from the east (flow towards −x).
const BOXES: Box[] = [
  { x0: 0, x1: 30, y0: 0, y1: 20 },
  { x0: 45, x1: 70, y0: -5, y1: 12 },
];

export interface PlanFields {
  K: Float32Array;
  ux: Float32Array;
  uy: Float32Array;
  speed: Float32Array;
  mask: Uint8Array;
  lawson: Uint8Array;
}

function inside(b: Box, x: number, y: number): boolean {
  return x >= b.x0 && x <= b.x1 && y >= b.y0 && y <= b.y1;
}

/** Potential-flow doublet around each block plus a decaying wake: looks like wind, costs nothing. */
function velocityAt(x: number, y: number): [number, number] {
  let u = -1;
  let v = 0;
  for (const b of BOXES) {
    const cx = (b.x0 + b.x1) / 2;
    const cy = (b.y0 + b.y1) / 2;
    const r = ((b.y1 - b.y0) / 2) * 1.15;
    const dx = x - cx;
    const dy = y - cy;
    const r2 = dx * dx + dy * dy;
    const k = (0.62 * r * r) / Math.max(r2 * r2, 1e-6);
    u += k * (dx * dx - dy * dy);
    v += k * 2 * dx * dy;
    const behind = b.x0 - x;
    const half = (b.y1 - b.y0) / 2;
    if (behind > 0) {
      const spread = half * (1 + behind / 40);
      const lateral = Math.exp(-((dy / spread) ** 4));
      const recovery = 1 - Math.exp(-behind / (3.2 * half));
      const factor = 1 - lateral * (1 - (0.08 + 0.92 * recovery));
      u *= factor;
      v = v * factor + lateral * 0.25 * Math.sin(behind / 6) * (1 - recovery);
    }
  }
  return [u, v];
}

/** Synthetic plan result on GRID; `calmer` applies the porous-screen alternative east of Torre A. */
export function synthPlan(calmer: boolean): PlanFields {
  const n = GRID.nx * GRID.ny;
  const f: PlanFields = {
    K: new Float32Array(n),
    ux: new Float32Array(n),
    uy: new Float32Array(n),
    speed: new Float32Array(n),
    mask: new Uint8Array(n),
    lawson: new Uint8Array(n),
  };
  for (let r = 0; r < GRID.ny; r += 1) {
    for (let c = 0; c < GRID.nx; c += 1) {
      const i = r * GRID.nx + c;
      const x = GRID.origin_x + (c + 0.5) * GRID.dx_m;
      const y = GRID.origin_y + (r + 0.5) * GRID.dx_m;
      if (BOXES.some((b) => inside(b, x, y))) {
        f.K[i] = f.ux[i] = f.uy[i] = f.speed[i] = Number.NaN;
        f.mask[i] = 1;
        f.lawson[i] = 255;
        continue;
      }
      let [u, v] = velocityAt(x, y);
      if (calmer) {
        const d = Math.hypot((x - 34) / 16, (y - 10) / 15);
        const damp = d < 1 ? 0.55 + 0.45 * d * d : 1;
        u *= damp;
        v *= damp;
        if (x > 30.5 && x < 31.5 && y >= 0 && y <= 20) f.mask[i] = 2;
      }
      const k = Math.hypot(u, v);
      f.K[i] = k;
      f.ux[i] = u * U_REF;
      f.uy[i] = v * U_REF;
      f.speed[i] = k * U_REF;
      f.lawson[i] = Math.min(4, Math.floor(k * 2.6));
    }
  }
  return f;
}

/** Section result (nz, ns), row 0 = ground: log profile with a block between s = 0 and 30. */
export function synthSection(ns: number, nz: number, s0: number): Float32Array {
  const out = new Float32Array(ns * nz);
  for (let z = 0; z < nz; z += 1) {
    for (let s = 0; s < ns; s += 1) {
      const sm = s0 + s + 0.5;
      const zm = z + 0.5;
      const i = z * ns + s;
      if (sm >= 0 && sm <= 30 && zm <= 36) {
        out[i] = Number.NaN;
        continue;
      }
      const profile = Math.log((zm + 0.5) / 0.5) / Math.log(60 / 0.5);
      const wake = sm > 30 && zm < 40 ? 1 - 0.85 * Math.exp(-(sm - 30) / 45) * Math.exp(-((zm / 40) ** 2)) : 1;
      const roof = zm > 36 && zm < 46 && sm > -5 && sm < 40 ? 1.25 : 1;
      out[i] = U_REF * 1.3 * profile * wake * roof;
    }
  }
  return out;
}

/** Float32Array → ArrayBuffer copy for HttpResponse.arrayBuffer. */
export function toBuffer(a: Float32Array | Uint8Array): ArrayBuffer {
  return a.buffer.slice(a.byteOffset, a.byteOffset + a.byteLength) as ArrayBuffer;
}
