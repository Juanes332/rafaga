/** A decoded result field, row-major (rows, cols); plan: row 0 = south, col 0 = west. */
export interface Field {
  rows: number;
  cols: number;
  dtype: "float32" | "uint8";
  data: Float32Array | Uint8Array;
}

function parseShape(header: string | null): [number, number] | null {
  if (!header) return null;
  const parts = header.split(",").map((s) => Number(s.trim()));
  return parts.length === 2 && parts.every((n) => Number.isInteger(n) && n > 0) ? [parts[0], parts[1]] : null;
}

/** Decode GET /results/{id}/fields/{name} (raw LE float32 or uint8, no header). */
export function decodeField(buffer: ArrayBuffer, headers: Headers, fallbackShape?: [number, number]): Field {
  const dtype = headers.get("X-Field-Dtype") === "uint8" ? "uint8" : "float32";
  const shape = parseShape(headers.get("X-Field-Shape")) ?? fallbackShape;
  const data = dtype === "uint8" ? new Uint8Array(buffer) : new Float32Array(buffer);
  if (!shape) throw new Error("field shape unknown");
  if (shape[0] * shape[1] !== data.length) throw new Error("field size mismatch");
  return { rows: shape[0], cols: shape[1], dtype, data };
}

/** Value of the cell containing grid coords (col, row) in cell units; NaN outside. */
export function sampleNearest(f: Field, col: number, row: number): number {
  const c = Math.floor(col);
  const r = Math.floor(row);
  if (c < 0 || r < 0 || c >= f.cols || r >= f.rows) return Number.NaN;
  return f.data[r * f.cols + c];
}

/** Bilinear interpolation between cell centres; (x, y) in cell units from the lower-left corner. */
export function sampleBilinear(f: Field, x: number, y: number): number {
  const gx = Math.max(0, Math.min(f.cols - 1, x - 0.5));
  const gy = Math.max(0, Math.min(f.rows - 1, y - 0.5));
  if (x < 0 || y < 0 || x > f.cols || y > f.rows) return Number.NaN;
  const c0 = Math.floor(gx);
  const r0 = Math.floor(gy);
  const c1 = Math.min(c0 + 1, f.cols - 1);
  const r1 = Math.min(r0 + 1, f.rows - 1);
  const tx = gx - c0;
  const ty = gy - r0;
  const at = (r: number, c: number) => f.data[r * f.cols + c];
  const top = at(r0, c0) * (1 - tx) + at(r0, c1) * tx;
  const bottom = at(r1, c0) * (1 - tx) + at(r1, c1) * tx;
  return top * (1 - ty) + bottom * ty;
}
