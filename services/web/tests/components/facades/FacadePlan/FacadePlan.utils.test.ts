import { describe, expect, it } from "vitest";
import { buildingEdges, planViewBox } from "@/components/facades/FacadePlan/FacadePlan.utils";
import { sampleBuildings } from "../../../msw/geometry/geometry.handlers";

describe("FacadePlan utils", () => {
  it("lists every edge with its length and outward normal (CCW footprint)", () => {
    const edges = buildingEdges(sampleBuildings()[0]);
    expect(edges).toHaveLength(4);
    expect(edges[0]).toMatchObject({ index: 0, length: 30 });
    // Edge 0 runs west→east along y = 0, so outward is south.
    expect(edges[0].normal[0]).toBeCloseTo(0);
    expect(edges[0].normal[1]).toBeCloseTo(-1);
  });
  it("frames all buildings with a margin and north up (y flipped)", () => {
    const vb = planViewBox(sampleBuildings(), 10);
    expect(vb).toEqual({ x: -10, y: -30, width: 90, height: 45 });
  });
});
