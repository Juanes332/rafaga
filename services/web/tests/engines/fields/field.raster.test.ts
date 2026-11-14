import { describe, expect, it } from "vitest";
import { kColor } from "@/engines/colormaps/colormap";
import { rasterize } from "@/engines/fields/field.raster";
import type { Field } from "@/engines/fields/field.decode";

describe("rasterize", () => {
  it("flips rows so north is up and leaves solid (NaN) cells transparent", () => {
    const f: Field = { rows: 2, cols: 1, dtype: "float32", data: new Float32Array([0, Number.NaN]) };
    const px = rasterize(f, kColor);
    // Top pixel row = northmost data row (NaN) → alpha 0.
    expect(px[3]).toBe(0);
    expect(Array.from(px.slice(4, 7))).toEqual(kColor(0));
    expect(px[7]).toBe(255);
  });
});
