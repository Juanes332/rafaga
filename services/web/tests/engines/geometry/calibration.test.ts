import { describe, expect, it } from "vitest";
import { measureMetres, metresPerPixel, relativeError } from "@/engines/geometry/calibration";

describe("plan calibration", () => {
  it("derives metres per pixel from two points and a real distance", () => {
    expect(metresPerPixel([0, 0], [300, 400], 25)).toBeCloseTo(0.05);
  });
  it("rejects degenerate calibrations", () => {
    expect(metresPerPixel([1, 1], [1, 1], 10)).toBeNull();
    expect(metresPerPixel([0, 0], [10, 0], 0)).toBeNull();
  });
  it("ruler on the calibrated points differs ≤1 % from the calibrated distance", () => {
    const p1: [number, number] = [137.4, 92.1];
    const p2: [number, number] = [811.9, 604.3];
    const mpp = metresPerPixel(p1, p2, 42.7) as number;
    const measured = measureMetres(p1, p2, mpp);
    expect(relativeError(measured, 42.7)).toBeLessThanOrEqual(0.01);
  });
  it("ruler stays within 1 % on another segment of known length", () => {
    // 1000 px span calibrated as 50 m: a 200 px span must read 10 m.
    const mpp = metresPerPixel([0, 0], [1000, 0], 50) as number;
    expect(relativeError(measureMetres([100, 100], [100, 300], mpp), 10)).toBeLessThanOrEqual(0.01);
  });
});
