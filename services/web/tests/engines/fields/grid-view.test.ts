import { describe, expect, it } from "vitest";
import { cellToEnu, cellToScreen, enuToCell, fitView, screenToCell, zoomAt } from "@/engines/fields/grid-view";

const grid = { origin_x: -40, origin_y: -50, dx_m: 1, nx: 160, ny: 120 };

describe("grid view", () => {
  it("fits the grid inside the canvas, centred, keeping square cells", () => {
    const v = fitView(160, 120, 800, 800, 0);
    expect(v.ppc).toBe(5);
    expect(v.ox).toBe(0);
    expect(v.oy).toBe(100);
    expect(v.zoom).toBe(1);
  });
  it("converts screen ↔ cell with north up", () => {
    const v = fitView(160, 120, 800, 600, 0);
    expect(screenToCell(v, 120, 0, 0)).toEqual([0, 120]);
    expect(screenToCell(v, 120, 800, 600)).toEqual([160, 0]);
    expect(cellToScreen(v, 120, 0, 0)).toEqual([0, 600]);
  });
  it("converts ENU metres ↔ cell units through the output grid", () => {
    expect(enuToCell(grid, 0, 0)).toEqual([40, 50]);
    expect(cellToEnu(grid, 40, 50)).toEqual([0, 0]);
  });
  it("zooms around the cursor keeping the point under it fixed", () => {
    const v = fitView(160, 120, 800, 600, 0);
    const z = zoomAt(v, 2, 400, 300);
    expect(z.zoom).toBe(2);
    expect(screenToCell(z, 120, 400, 300)).toEqual(screenToCell(v, 120, 400, 300));
  });
});
