import { describe, expect, it } from "vitest";
import { needsCpuConfirmation } from "@/components/simulations/CpuWarningDialog/CpuWarningDialog.utils";
import type { Estimate } from "@/types/simulations/simulation.types";

const base: Estimate = { device: "cpu", nodes: 1, memory_bytes: 1, budget_bytes: 2, fits: true, proposed_dx_m: null, rejected_reason: null, eta_seconds: 7200 };

describe("needsCpuConfirmation", () => {
  it("requires confirmation for a 3D run that will compute on CPU", () => {
    expect(needsCpuConfirmation("volume3d", base)).toBe(true);
  });
  it("does not for 3D on GPU", () => {
    expect(needsCpuConfirmation("volume3d", { ...base, device: "gpu" })).toBe(false);
  });
  it("does not for 2D on CPU", () => {
    expect(needsCpuConfirmation("plan2d", base)).toBe(false);
  });
  it("does not when the solver is offline (device unknown) or no estimate yet", () => {
    expect(needsCpuConfirmation("volume3d", { ...base, rejected_reason: "solver_offline" })).toBe(false);
    expect(needsCpuConfirmation("volume3d", undefined)).toBe(false);
  });
});
