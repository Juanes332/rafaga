import { describe, expect, it } from "vitest";
import { coverage, dominantDirections, petalColor, sectorArcs } from "@/components/wind/WindRose/WindRose.utils";
import { eraSectors } from "../../../msw/wind/wind.fixtures";

describe("WindRose utils", () => {
  it("builds 16 petals, longest for the most frequent sector", () => {
    const arcs = sectorArcs(eraSectors(), 100, 10);
    expect(arcs).toHaveLength(16);
    const longest = arcs.reduce((a, b) => (b.outer > a.outer ? b : a));
    expect(longest.deg).toBe(90);
    expect(longest.outer).toBe(100);
  });
  it("sums the frequency of selected directions", () => {
    expect(coverage(eraSectors(), [90, 67.5])).toBeCloseTo(0.35);
    expect(coverage(null, [90])).toBeNull();
  });
  it("picks the most frequent directions until they cover the target share", () => {
    expect(dominantDirections(eraSectors(), 0.5)).toEqual([90, 67.5, 112.5, 45]);
  });
  it("colours petals with the speed LUT", () => {
    expect(petalColor(0)).toMatch(/^rgb\(/);
  });
});
