import { describe, expect, it } from "vitest";
import { ZONE, classifyZones, largestBlob, reductionZones, zoneAreas } from "@/engines/fields/zones";
import type { Field } from "@/engines/fields/field.decode";

const f = (rows: number, cols: number, values: number[]): Field => ({ rows, cols, dtype: "float32", data: new Float32Array(values) });

describe("zones (client-side re-thresholding)", () => {
  it("classifies acceleration above k_accel and stagnation below k_stagnation; solids get none", () => {
    const codes = classifyZones(f(1, 4, [1.5, 0.1, 0.8, Number.NaN]), { k_accel: 1.2, k_stagnation: 0.3 });
    expect(Array.from(codes)).toEqual([ZONE.acceleration, ZONE.stagnation, ZONE.none, ZONE.solid]);
  });
  it("moves with the thresholds without re-simulating", () => {
    const codes = classifyZones(f(1, 2, [1.25, 0.35]), { k_accel: 1.3, k_stagnation: 0.4 });
    expect(Array.from(codes)).toEqual([ZONE.none, ZONE.stagnation]);
  });
  it("marks reduction where ΔK is below the (negative) threshold", () => {
    expect(Array.from(reductionZones(f(1, 3, [-0.2, -0.05, Number.NaN]), -0.1))).toEqual([ZONE.reduction, ZONE.none, ZONE.solid]);
  });
  it("computes areas in m² and percent of fluid area", () => {
    const codes = new Uint8Array([ZONE.acceleration, ZONE.acceleration, ZONE.none, ZONE.solid]);
    const areas = zoneAreas(codes, 2);
    expect(areas.fluidM2).toBe(12);
    expect(areas.acceleration).toEqual({ area_m2: 8, percent: (8 / 12) * 100 });
    expect(areas.stagnation.area_m2).toBe(0);
  });
  it("finds the largest connected blob and its centroid for the label", () => {
    // 3×4 grid: blob of 3 on the left, 1 cell on the right.
    const codes = new Uint8Array([1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0]);
    expect(largestBlob(codes, 4, 3, 1)).toEqual({ cells: 3, col: 0.5, row: 1.5 });
    expect(largestBlob(codes, 4, 3, 2)).toBeNull();
  });
});
