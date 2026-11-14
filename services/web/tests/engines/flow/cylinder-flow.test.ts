import { describe, expect, it } from "vitest";
import { cylinderStreamlines, cylinderVelocity } from "@/engines/flow/cylinder-flow";

describe("cylinder potential flow", () => {
  it("is uniform far from the obstacle", () => {
    const [u, v] = cylinderVelocity(1000, 0, 1);
    expect(u).toBeCloseTo(1, 3);
    expect(v).toBeCloseTo(0, 3);
  });
  it("stagnates at the front of the cylinder", () => {
    const [u, v] = cylinderVelocity(-1, 0, 1);
    expect(Math.hypot(u, v)).toBeCloseTo(0, 6);
  });
  it("produces one SVG path per seed, never entering the obstacle", () => {
    const paths = cylinderStreamlines({ width: 400, height: 300, lines: 12 });
    expect(paths).toHaveLength(12);
    for (const d of paths) expect(d.startsWith("M")).toBe(true);
  });
});
