import { describe, expect, it } from "vitest";
import { cameraFor, fieldMax, sliceRgba } from "@/components/viewer3d/ResultsViewer3D/ResultsViewer3D.utils";
import { lutRgb, SPEED_LUT } from "@/engines/colormaps/colormap";

const f = { rows: 2, cols: 1, dtype: "float32" as const, data: new Float32Array([0, Number.NaN]) };

describe("3D viewer utils", () => {
  it("keeps the ground row at the bottom and solids transparent", () => {
    const px = sliceRgba(f, 4);
    expect(Array.from(px.slice(0, 3))).toEqual(lutRgb(SPEED_LUT, 0));
    expect(px[7]).toBe(0);
  });
  it("rounds the colour domain up to whole m/s", () => {
    expect(fieldMax([{ ...f, data: new Float32Array([2.2, 3.4]) }])).toBe(4);
  });
  it("looks at the buildings' centre from the south-east", () => {
    const c = cameraFor({ min: [0, 0, 0], max: [20, 10, 30] });
    expect(c.target).toEqual([10, 0, -5]);
    expect(c.position[0]).toBeGreaterThan(10);
  });
});
