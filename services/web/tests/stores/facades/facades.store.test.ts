import { beforeEach, describe, expect, it } from "vitest";
import { useFacadesStore } from "@/stores/facades/facades.store";

describe("facades store", () => {
  beforeEach(() => useFacadesStore.getState().reset());

  it("starts with nothing selected", () => {
    expect(useFacadesStore.getState()).toMatchObject({ alternativeId: null, edge: null });
  });
  it("selects an alternative and clears the edge", () => {
    useFacadesStore.getState().selectEdge({ buildingId: "b", edgeIndex: 1 });
    useFacadesStore.getState().selectAlternative("a2");
    expect(useFacadesStore.getState()).toMatchObject({ alternativeId: "a2", edge: null });
  });
  it("toggles the same edge off", () => {
    const edge = { buildingId: "b", edgeIndex: 1 };
    useFacadesStore.getState().selectEdge(edge);
    useFacadesStore.getState().selectEdge(edge);
    expect(useFacadesStore.getState().edge).toBeNull();
  });
});
