import { describe, expect, it } from "vitest";
import { clientToWorld, computeViewBox, niceScaleBar, toSvgPoints } from "@/components/geometry/PlanCanvas/PlanCanvas.utils";

describe("plan canvas maths", () => {
  it("fits content with a margin and keeps north up (svg y = −north)", () => {
    const vb = computeViewBox({ minX: 0, minY: 0, maxX: 100, maxY: 50 }, 1, [0, 0]);
    expect(vb.x).toBeLessThan(0);
    expect(vb.y).toBeLessThan(-50);
    expect(vb.w).toBeGreaterThan(100);
  });
  it("falls back to a 100 m square around the origin when empty", () => {
    expect(computeViewBox(null, 1, [0, 0])).toEqual({ x: -50, y: -50, w: 100, h: 100 });
  });
  it("zooms about the centre and pans in metres", () => {
    const vb = computeViewBox(null, 2, [10, 0]);
    expect(vb).toEqual({ x: -15, y: -25, w: 50, h: 50 });
  });
  it("widens the view box to the canvas aspect", () => {
    expect(computeViewBox(null, 1, [0, 0], 2)).toEqual({ x: -100, y: -50, w: 200, h: 100 });
  });
  it("maps client pixels to world metres under xMidYMid meet", () => {
    const vb = { x: 0, y: -100, w: 100, h: 100 };
    const rect = { left: 0, top: 0, width: 400, height: 200 };
    // Content is 200×200 px, centred: x offset 100 px.
    expect(clientToWorld(200, 100, rect, vb)).toEqual([50, 50]);
    expect(clientToWorld(100, 200, rect, vb)).toEqual([0, 0]);
  });
  it("flips y for svg points", () => {
    expect(toSvgPoints([[0, 0], [10, 5]])).toBe("0,0 10,-5");
  });
  it("picks a round scale-bar length", () => {
    expect(niceScaleBar(180)).toBe(20);
    expect(niceScaleBar(30)).toBe(5);
    expect(niceScaleBar(2000)).toBe(500);
  });
});

describe("grid", () => {
  it("draws one line per step in each direction", async () => {
    const { gridPath } = await import("@/components/geometry/PlanCanvas/PlanCanvas.utils");
    const d = gridPath({ x: 0, y: 0, w: 20, h: 10 }, 10);
    expect(d.match(/M/g)).toHaveLength(3 + 2);
  });
});
