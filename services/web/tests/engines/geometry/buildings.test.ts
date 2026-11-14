import { describe, expect, it } from "vitest";
import {
  DEFAULT_HEIGHT_M,
  addBuilding,
  clientIssues,
  moveBuilding,
  removeBuilding,
  scaleBuilding,
  updateBuilding,
} from "@/engines/geometry/buildings";
import { signedArea } from "@/engines/geometry/polygon";
import type { Building } from "@/types/geometry/geometry.types";

const b = (id: string, footprint: number[][], height_m: number | null = 10): Building => ({
  id,
  footprint,
  holes: [],
  height_m,
  source: "draw",
  missing_height: false,
});

describe("building operations", () => {
  it("adds a drawn block with the 12 m default height and a CCW footprint", () => {
    const [added] = addBuilding([], [[0, 0], [0, 10], [10, 10], [10, 0]], "Bloque 1");
    expect(added.height_m).toBe(DEFAULT_HEIGHT_M);
    expect(DEFAULT_HEIGHT_M).toBe(12);
    expect(signedArea(added.footprint)).toBeGreaterThan(0);
    expect(added.source).toBe("draw");
  });
  it("updates, moves, scales and removes without mutating the input", () => {
    const list = [b("a", [[0, 0], [10, 0], [10, 10], [0, 10]])];
    expect(updateBuilding(list, "a", { height_m: 30 })[0].height_m).toBe(30);
    expect(moveBuilding(list, "a", 2, 3)[0].footprint[0]).toEqual([2, 3]);
    expect(scaleBuilding(list, "a", 2)[0].footprint[0]).toEqual([-5, -5]);
    expect(removeBuilding(list, "a")).toEqual([]);
    expect(list[0].footprint[0]).toEqual([0, 0]);
  });
  it("clears missing_height once a height is set", () => {
    const list = [{ ...b("a", [[0, 0], [1, 0], [1, 1]], null), missing_height: true }];
    expect(updateBuilding(list, "a", { height_m: 9 })[0].missing_height).toBe(false);
  });
  it("flags self-intersections, heights out of range and missing heights client-side", () => {
    const issues = clientIssues([
      b("bow", [[0, 0], [10, 10], [10, 0], [0, 10]]),
      b("tall", [[0, 0], [10, 0], [10, 10]], 900),
      b("none", [[0, 0], [10, 0], [10, 10]], null),
    ]);
    expect(issues.map((i) => [i.building_id, i.code])).toEqual([
      ["bow", "self_intersection"],
      ["tall", "height_out_of_range"],
      ["none", "missing_height"],
    ]);
  });
});
