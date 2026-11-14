import { describe, expect, it } from "vitest";
import {
  bbox,
  ensureCcw,
  nearestEdge,
  pointInPolygon,
  polygonArea,
  rectFromCorners,
  scaleAbout,
  selfIntersects,
  signedArea,
  snap,
  translate,
} from "@/engines/geometry/polygon";

const square = [[0, 0], [10, 0], [10, 10], [0, 10]];

describe("polygon math", () => {
  it("computes signed and absolute area", () => {
    expect(signedArea(square)).toBe(100);
    expect(signedArea([...square].reverse())).toBe(-100);
    expect(polygonArea([...square].reverse())).toBe(100);
  });
  it("orients rings counter-clockwise", () => {
    expect(signedArea(ensureCcw([...square].reverse()))).toBeGreaterThan(0);
    expect(ensureCcw(square)).toEqual(square);
  });
  it("detects self-intersection (bow tie) but not a valid ring", () => {
    expect(selfIntersects([[0, 0], [10, 10], [10, 0], [0, 10]])).toBe(true);
    expect(selfIntersects(square)).toBe(false);
    expect(selfIntersects([[0, 0], [10, 0], [10, 10], [5, 2], [0, 10]])).toBe(false);
  });
  it("tests point containment", () => {
    expect(pointInPolygon([5, 5], square)).toBe(true);
    expect(pointInPolygon([15, 5], square)).toBe(false);
  });
  it("snaps to the grid step", () => {
    expect(snap([1.4, 2.6], 1)).toEqual([1, 3]);
    expect(snap([1.4, 2.6], 0)).toEqual([1.4, 2.6]);
  });
  it("builds a CCW rectangle from any two corners", () => {
    const r = rectFromCorners([10, 10], [0, 0]);
    expect(polygonArea(r)).toBe(100);
    expect(signedArea(r)).toBeGreaterThan(0);
  });
  it("translates and scales about a point", () => {
    expect(translate(square, 1, 2)[0]).toEqual([1, 2]);
    expect(polygonArea(scaleAbout(square, [5, 5], 2))).toBe(400);
  });
  it("returns the bounding box", () => {
    expect(bbox([square, [[20, -5], [21, -5], [21, 0]]])).toEqual({ minX: 0, minY: -5, maxX: 21, maxY: 10 });
  });
  it("finds the nearest edge index and distance", () => {
    expect(nearestEdge([5, -1], square)).toEqual({ index: 0, distance: 1 });
    expect(nearestEdge([11, 5], square).index).toBe(1);
  });
});
