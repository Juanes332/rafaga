import { beforeEach, describe, expect, it } from "vitest";
import { nextPosition, useCompareStore } from "@/stores/compare/compare.store";

describe("compare store", () => {
  beforeEach(() => useCompareStore.getState().reset());

  it("starts centred, split view, zones off", () => {
    expect(useCompareStore.getState()).toMatchObject({ position: 50, deltaK: false, zones: false });
  });
  it("moves 2 % per arrow and 10 % with Shift, clamped to 0–100", () => {
    expect(nextPosition(50, "ArrowRight", false)).toBe(52);
    expect(nextPosition(50, "ArrowLeft", true)).toBe(40);
    expect(nextPosition(99, "ArrowRight", true)).toBe(100);
    expect(nextPosition(10, "Home", false)).toBe(0);
    expect(nextPosition(10, "End", false)).toBe(100);
    expect(nextPosition(10, "a", false)).toBe(10);
  });
  it("clamps dragged positions", () => {
    useCompareStore.getState().setPosition(130);
    expect(useCompareStore.getState().position).toBe(100);
  });
  it("toggles ΔK and zones", () => {
    useCompareStore.getState().toggleDeltaK();
    useCompareStore.getState().toggleZones();
    expect(useCompareStore.getState()).toMatchObject({ deltaK: true, zones: true });
  });
});
