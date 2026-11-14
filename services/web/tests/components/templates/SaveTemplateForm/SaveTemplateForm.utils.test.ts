import { describe, expect, it } from "vitest";
import { buildPayload, FALLBACK_TERRAIN } from "@/components/templates/SaveTemplateForm/SaveTemplateForm.utils";
import { defaultSettings } from "../../../msw/settings/settings.handlers";

describe("template payload", () => {
  it("falls back to urban terrain when the project has no wind", () => {
    const p = buildPayload(defaultSettings(), null, []);
    expect(p).toMatchObject(FALLBACK_TERRAIN);
  });
  it("copies the project's terrain and never a location key", () => {
    const p = buildPayload(defaultSettings(), { source: "manual", rose: null, terrain_category: "open", z0_m: 0.03, from_cache: false, period_years: 10 }, []);
    expect(p.z0_m).toBe(0.03);
    expect(Object.keys(p).sort()).toEqual(["facade_defaults", "lawson", "terrain_category", "thresholds", "z0_m"]);
  });
});
