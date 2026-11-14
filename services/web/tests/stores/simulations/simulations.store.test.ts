import { beforeEach, describe, expect, it } from "vitest";
import { useSimulationFormStore } from "@/stores/simulations/simulations.store";

describe("simulation form store", () => {
  beforeEach(() => useSimulationFormStore.getState().forProject("p1"));

  it("starts with plan 2D, 1 m cells, automatic device and no direction", () => {
    expect(useSimulationFormStore.getState()).toMatchObject({ kind: "plan2d", dxM: 1, device: "auto", directions: [] });
  });
  it("toggles directions and keeps them sorted", () => {
    const s = useSimulationFormStore.getState();
    s.toggleDirection(90);
    s.toggleDirection(45);
    expect(useSimulationFormStore.getState().directions).toEqual([45, 90]);
    useSimulationFormStore.getState().toggleDirection(90);
    expect(useSimulationFormStore.getState().directions).toEqual([45]);
  });
  it("resets when another project is opened", () => {
    useSimulationFormStore.getState().setDirections([90]);
    useSimulationFormStore.getState().forProject("p2");
    expect(useSimulationFormStore.getState().directions).toEqual([]);
  });
  it("keeps the state when the same project is reopened", () => {
    useSimulationFormStore.getState().setDx(2);
    useSimulationFormStore.getState().forProject("p1");
    expect(useSimulationFormStore.getState().dxM).toBe(2);
  });
});
