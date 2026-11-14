import { beforeEach, describe, expect, it } from "vitest";
import { HISTORY_LIMIT, useGeometryStore } from "@/stores/geometry/geometry.store";
import type { Building } from "@/types/geometry/geometry.types";

const block = (id: string, h = 10): Building => ({ id, footprint: [[0, 0], [1, 0], [1, 1]], holes: [], height_m: h, source: "draw", missing_height: false });
const s = () => useGeometryStore.getState();

describe("geometry editor store", () => {
  beforeEach(() => s().load("p", { version: 2, buildings: [block("a")], issues: [] }));

  it("loads server geometry as a clean draft", () => {
    expect(s()).toMatchObject({ projectId: "p", baseVersion: 2, dirty: false, past: [], future: [] });
  });

  it("applies, undoes and redoes", () => {
    s().apply([block("a", 20)]);
    expect(s().dirty).toBe(true);
    s().undo();
    expect(s().buildings[0].height_m).toBe(10);
    s().redo();
    expect(s().buildings[0].height_m).toBe(20);
  });

  it("keeps at least 50 undo levels", () => {
    for (let i = 0; i < 60; i += 1) s().apply([block("a", 11 + i)]);
    expect(HISTORY_LIMIT).toBeGreaterThanOrEqual(50);
    for (let i = 0; i < 50; i += 1) s().undo();
    expect(s().buildings[0].height_m).toBe(20);
  });

  it("drops the redo branch after a new edit", () => {
    s().apply([block("a", 20)]);
    s().undo();
    s().apply([block("a", 30)]);
    expect(s().future).toEqual([]);
  });

  it("clears the selection when the selected block disappears on undo", () => {
    s().apply([block("a"), block("b")]);
    s().select("b");
    s().undo();
    expect(s().selectedId).toBeNull();
  });

  it("marks saved with the new version", () => {
    s().apply([block("a", 20)]);
    s().markSaved(3);
    expect(s()).toMatchObject({ baseVersion: 3, dirty: false });
  });

  it("switches tools and clears selection when drawing", () => {
    s().select("a");
    s().setTool("rect");
    expect(s()).toMatchObject({ tool: "rect", selectedId: null });
  });

  it("zooms within range, pans and resets the view", () => {
    s().zoomBy(1000);
    expect(s().zoom).toBe(20);
    s().panBy(5, -2);
    expect(s().pan).toEqual([5, -2]);
    s().resetView();
    expect(s()).toMatchObject({ zoom: 1, pan: [0, 0] });
  });

  it("starts another project in the plan view with the selection tool", () => {
    s().setTool("polygon");
    s().setView("3d");
    s().load("q", { version: 1, buildings: [], issues: [] });
    expect(s()).toMatchObject({ tool: "select", view: "plan" });
  });
});
