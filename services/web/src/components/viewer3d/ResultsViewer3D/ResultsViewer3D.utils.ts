import { lutIndex, lutRgb, SPEED_LUT } from "@/engines/colormaps/colormap";
import type { Field } from "@/engines/fields/field.decode";

/** RGBA for a vertical slice, row 0 = ground at the bottom of the plane (no flip). */
export function sliceRgba(f: Field, max: number): Uint8Array {
  const out = new Uint8Array(f.rows * f.cols * 4);
  for (let i = 0; i < f.data.length; i += 1) {
    const v = f.data[i];
    if (!Number.isFinite(v)) continue;
    const [r, g, b] = lutRgb(SPEED_LUT, lutIndex(v, [0, max]));
    out.set([r, g, b, 235], i * 4);
  }
  return out;
}

export function fieldMax(fields: Array<Field | undefined>): number {
  let m = 1;
  for (const f of fields) if (f) for (const v of f.data) if (Number.isFinite(v) && v > m) m = v;
  return Math.ceil(m);
}

export interface Bounds {
  min: [number, number, number];
  max: [number, number, number];
}

/** Camera placed south-east and above, looking at the centre of the base buildings. */
export function cameraFor(b: Bounds): { position: [number, number, number]; target: [number, number, number] } {
  const cx = (b.min[0] + b.max[0]) / 2;
  const cy = (b.min[1] + b.max[1]) / 2;
  const span = Math.max(b.max[0] - b.min[0], b.max[1] - b.min[1], b.max[2]) * 2.2 + 40;
  // three.js world = (x, z, −y) of ENU.
  return { position: [cx + span * 0.7, span * 0.6, -cy + span * 0.7], target: [cx, 0, -cy] };
}
