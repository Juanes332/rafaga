import { describe, expect, it } from "vitest";
import { availableLayers, exportPhase } from "@/components/exports/ExportDialog/ExportDialog.utils";

describe("export dialog utils", () => {
  it("adds ΔK only with a comparison result", () => {
    expect(availableLayers(null)).not.toContain("delta_k");
    expect(availableLayers("r2")).toContain("delta_k");
  });
  it("derives the phase", () => {
    expect(exportPhase(null, false, undefined)).toBe("idle");
    expect(exportPhase(null, true, undefined)).toBe("running");
    expect(exportPhase("e", false, { id: "e", status: "running", file_ready: false })).toBe("running");
    expect(exportPhase("e", false, { id: "e", status: "completed", file_ready: true })).toBe("ready");
    expect(exportPhase("e", false, { id: "e", status: "failed", file_ready: false })).toBe("failed");
  });
});
