import { describe, expect, it } from "vitest";
import { computeStreamlines, seedGrid, traceStreamline, type VectorField } from "@/engines/streamlines/streamlines";

function uniform(cols: number, rows: number, u: number, v: number, solid?: (c: number, r: number) => boolean): VectorField {
  const U = new Float32Array(cols * rows).fill(u);
  const V = new Float32Array(cols * rows).fill(v);
  if (solid) for (let r = 0; r < rows; r += 1) for (let c = 0; c < cols; c += 1) if (solid(c, r)) U[r * cols + c] = V[r * cols + c] = Number.NaN;
  return { cols, rows, u: U, v: V };
}

describe("streamlines (RK2 fallback)", () => {
  it("follows a uniform field in a straight line", () => {
    const line = traceStreamline(uniform(20, 10, 1, 0), 2, 5, { step: 0.5, maxSteps: 10 });
    expect(line.length).toBeGreaterThan(4);
    for (let i = 1; i < line.length; i += 2) expect(line[i]).toBeCloseTo(5);
    expect(line[line.length - 2]).toBeGreaterThan(line[0]);
  });
  it("stops at the grid edge and at solid cells", () => {
    const line = traceStreamline(uniform(20, 10, 1, 0, (c) => c >= 10), 2, 5, { step: 0.5, maxSteps: 500 });
    expect(Math.max(...line.filter((_, i) => i % 2 === 0))).toBeLessThan(10.5);
  });
  it("seeds on a regular spacing inside the grid", () => {
    const seeds = seedGrid(48, 24, 12);
    expect(seeds).toHaveLength(4 * 2);
    expect(seeds[0]).toEqual([6, 6]);
  });
  it("traces both ways from seeds and drops degenerate lines", () => {
    const lines = computeStreamlines(uniform(48, 24, 0, 0), 12);
    expect(lines).toEqual([]);
    expect(computeStreamlines(uniform(48, 24, 1, 0.2), 12).length).toBeGreaterThan(0);
  });
});
