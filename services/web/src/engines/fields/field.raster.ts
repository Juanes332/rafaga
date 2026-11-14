import type { Rgb } from "@/engines/colormaps/colormap";
import type { Field } from "./field.decode";

/**
 * RGBA pixels for a field, one pixel per cell, north up (row 0 = south is drawn last).
 * NaN (solid) cells are transparent so buildings show through.
 */
export function rasterize(f: Field, color: (v: number) => Rgb, alpha = 255): Uint8ClampedArray {
  const out = new Uint8ClampedArray(f.rows * f.cols * 4);
  for (let r = 0; r < f.rows; r += 1) {
    const dst = (f.rows - 1 - r) * f.cols;
    for (let c = 0; c < f.cols; c += 1) {
      const v = f.data[r * f.cols + c];
      const o = (dst + c) * 4;
      if (!Number.isFinite(v)) continue;
      const [red, green, blue] = color(v);
      out[o] = red;
      out[o + 1] = green;
      out[o + 2] = blue;
      out[o + 3] = alpha;
    }
  }
  return out;
}

/** Cell-wise b − a (ADR-23 common output grid); NaN where either is solid. */
export function subtractFields(a: Field, b: Field): Field {
  if (a.rows !== b.rows || a.cols !== b.cols) throw new Error("fields not comparable");
  const data = new Float32Array(a.data.length);
  for (let i = 0; i < data.length; i += 1) data[i] = b.data[i] - a.data[i];
  return { rows: a.rows, cols: a.cols, dtype: "float32", data };
}
