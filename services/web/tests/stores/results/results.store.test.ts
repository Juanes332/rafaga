import { beforeEach, describe, expect, it } from "vitest";
import { useResultsStore } from "@/stores/results/results.store";

describe("results store", () => {
  beforeEach(() => useResultsStore.getState().reset());

  it("starts on the K layer with particles running and no zones", () => {
    expect(useResultsStore.getState()).toMatchObject({ layer: "k", zones: false, paused: false, tool: "none" });
  });
  it("switches layer, zones and pause", () => {
    const s = useResultsStore.getState();
    s.setLayer("lawson");
    s.toggleZones();
    s.togglePaused();
    expect(useResultsStore.getState()).toMatchObject({ layer: "lawson", zones: true, paused: true });
  });
  it("collects two section points then stops", () => {
    const s = useResultsStore.getState();
    s.setTool("section");
    s.addSectionPoint([1, 2]);
    s.addSectionPoint([3, 4]);
    s.addSectionPoint([5, 6]);
    expect(useResultsStore.getState().section).toEqual([[1, 2], [3, 4]]);
  });
  it("clears the section when the tool closes", () => {
    const s = useResultsStore.getState();
    s.setTool("section");
    s.addSectionPoint([1, 2]);
    s.setTool("none");
    expect(useResultsStore.getState().section).toEqual([]);
  });
});
