import { describe, expect, it } from "vitest";
import {
  FrameBudget,
  buildVelocityData,
  particleCount,
  particleStep,
  upwindEdge,
  viewTransform,
} from "@/engines/particles/particles.math";

describe("particle engine math (WEB-03)", () => {
  it("uses 16 384 particles by default, 8 192 on narrow screens, 32 768 on fast hi-dpi", () => {
    expect(particleCount({ width: 1280, dpr: 1, meanFrameMs: null })).toBe(16384);
    expect(particleCount({ width: 600, dpr: 2, meanFrameMs: 5 })).toBe(8192);
    expect(particleCount({ width: 1440, dpr: 2, meanFrameMs: 6 })).toBe(32768);
  });

  it("keeps the density near one particle per 60 px² of canvas", () => {
    expect(particleCount({ width: 1440, dpr: 1, meanFrameMs: null, area: 860 * 640 })).toBe(9216);
    expect(particleCount({ width: 1440, dpr: 1, meanFrameMs: null, area: 4000 * 3000 })).toBe(16384);
  });

  it("moves K × 0.6 px per frame at zoom 1, capped at 3 px", () => {
    expect(particleStep(1, 1)).toBeCloseTo(0.6);
    expect(particleStep(1.5, 2)).toBeCloseTo(1.8);
    expect(particleStep(2, 4)).toBe(3);
  });

  it("builds an RG velocity texture as direction × K, zero in solids, and lists fluid cells", () => {
    const K = new Float32Array([2, Number.NaN, 0.5, 1]);
    const ux = new Float32Array([3, Number.NaN, 0, -1]);
    const uy = new Float32Array([4, Number.NaN, 2, 0]);
    const d = buildVelocityData(K, ux, uy, 2, 2);
    expect(Array.from(d.velocity.slice(0, 4))).toEqual([expect.closeTo(1.2), expect.closeTo(1.6), 0, 0]);
    expect(d.fluidCount).toBe(3);
    expect(Array.from(d.fluid.slice(0, 2))).toEqual([0.5, 0.5]);
  });

  it("degrades when the mean of 30 frames exceeds 20 ms", () => {
    const b = new FrameBudget();
    for (let i = 0; i < 29; i += 1) b.push(25);
    expect(b.shouldDegrade()).toBe(false);
    b.push(25);
    expect(b.shouldDegrade()).toBe(true);
    expect(b.shouldDegrade()).toBe(false);
  });

  it("places the upwind respawn edge against the mean flow", () => {
    // Flow towards −x (wind from the east): particles re-enter on the east edge.
    expect(upwindEdge(-1, 0, 100, 50)).toEqual([99.5, 0, 99.5, 50]);
    expect(upwindEdge(0, 1, 100, 50)).toEqual([0, 0.5, 100, 0.5]);
  });

  it("maps cells to clip space with north up", () => {
    const v = viewTransform({ cols: 10, rows: 5, width: 200, height: 100, ppc: 20, ox: 0, oy: 0 });
    // Cell (0,0) south-west corner → bottom-left of the canvas.
    expect(0 * v[0] + v[2]).toBeCloseTo(-1);
    expect(0 * v[1] + v[3]).toBeCloseTo(-1);
    expect(10 * v[0] + v[2]).toBeCloseTo(1);
    expect(5 * v[1] + v[3]).toBeCloseTo(1);
  });
});
