import { describe, expect, it } from "vitest";
import { computeSteps, stepFromPath } from "@/components/workspace/StepRail/StepRail.utils";

const facts = { hasLocation: false, buildingCount: 0, hasWind: false, alternativeCount: 1, completedStudies: 0, current: "location" as const };

describe("step states", () => {
  it("locks Viento and Simular until the location is set, with the reason", () => {
    const steps = computeSteps(facts);
    expect(steps.find((s) => s.key === "wind")).toMatchObject({ state: "locked", reasonKey: "workspace:steps.lockedLocation" });
    expect(steps.find((s) => s.key === "simulate")?.state).toBe("locked");
    expect(steps.find((s) => s.key === "location")?.state).toBe("current");
  });
  it("marks completed steps and unlocks with a location", () => {
    const steps = computeSteps({ ...facts, hasLocation: true, buildingCount: 2, current: "wind" });
    expect(steps.map((s) => s.state)).toEqual(["done", "done", "current", "todo", "todo", "locked"]);
  });
  it("unlocks Comparar with two completed studies", () => {
    expect(computeSteps({ ...facts, hasLocation: true, completedStudies: 2 }).at(-1)?.state).toBe("todo");
  });
  it("maps paths to steps", () => {
    expect(stepFromPath("/projects/p/wind")).toBe("wind");
    expect(stepFromPath("/projects/p/results/r")).toBe("simulate");
    expect(stepFromPath("/projects")).toBeNull();
  });
});
