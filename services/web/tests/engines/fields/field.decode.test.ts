import { describe, expect, it } from "vitest";
import { decodeField, sampleBilinear, sampleNearest } from "@/engines/fields/field.decode";

describe("field decoding", () => {
  it("reads little-endian float32 with the X-Field-Shape header", () => {
    const buf = new Float32Array([1, 2, 3, 4, 5, 6]).buffer;
    const f = decodeField(buf, new Headers({ "X-Field-Shape": "2,3", "X-Field-Dtype": "float32" }));
    expect(f).toMatchObject({ rows: 2, cols: 3, dtype: "float32" });
    expect(Array.from(f.data)).toEqual([1, 2, 3, 4, 5, 6]);
  });
  it("reads uint8 masks", () => {
    const f = decodeField(new Uint8Array([0, 1, 2, 0]).buffer, new Headers({ "X-Field-Shape": "2,2", "X-Field-Dtype": "uint8" }));
    expect(f.dtype).toBe("uint8");
    expect(Array.from(f.data)).toEqual([0, 1, 2, 0]);
  });
  it("falls back to an explicit shape when the header is missing", () => {
    const f = decodeField(new Float32Array(4).buffer, new Headers(), [2, 2]);
    expect(f.rows).toBe(2);
  });
  it("samples by cell (row 0 = south) and bilinearly between centres", () => {
    const f = decodeField(new Float32Array([0, 1, 2, 3]).buffer, new Headers({ "X-Field-Shape": "2,2" }));
    expect(sampleNearest(f, 1, 0)).toBe(1);
    expect(sampleBilinear(f, 0.5, 0.5)).toBe(0);
    expect(sampleBilinear(f, 1, 1)).toBeCloseTo(1.5);
  });
  it("returns NaN outside the grid", () => {
    const f = decodeField(new Float32Array([0, 1, 2, 3]).buffer, new Headers({ "X-Field-Shape": "2,2" }));
    expect(sampleNearest(f, 5, 0)).toBeNaN();
  });
});
