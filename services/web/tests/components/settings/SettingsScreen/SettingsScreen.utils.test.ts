import { describe, expect, it } from "vitest";
import { ApiError } from "@/lib/http/api-error";
import { orderErrors, serverFieldErrors, toPatch, withPath } from "@/components/settings/SettingsScreen/SettingsScreen.utils";
import { defaultSettings } from "../../../msw/settings/settings.handlers";

describe("settings utils", () => {
  it("updates a nested value immutably", () => {
    const s = defaultSettings();
    const next = withPath(s, ["lawson", "comfort", 1, "threshold_ms"], 7);
    expect(next.lawson.comfort[1].threshold_ms).toBe(7);
    expect(s.lawson.comfort[1].threshold_ms).toBe(6);
  });
  it("flags zone and Lawson ordering errors", () => {
    const s = defaultSettings();
    expect(orderErrors(s)).toEqual({ zones: false, lawson: false });
    expect(orderErrors(withPath(s, ["thresholds", "k_stagnation"], 1.5))).toMatchObject({ zones: true });
    expect(orderErrors(withPath(s, ["lawson", "safety", 1, "threshold_ms"], 12))).toMatchObject({ lawson: true });
  });
  it("maps 422 locations to field paths, dropping 'body'", () => {
    const err = new ApiError(422, "validation_error", "x", { errors: [{ loc: ["body", "thresholds", "k_accel"], type: "x" }] });
    expect(serverFieldErrors(err)).toEqual(["thresholds.k_accel"]);
    expect(serverFieldErrors(new Error("x"))).toEqual([]);
  });
  it("builds a full patch", () => {
    expect(Object.keys(toPatch(defaultSettings()))).toEqual([
      "thresholds",
      "lawson",
      "turbulence_intensity_default",
      "vegetation_cd",
      "alternatives_limit",
    ]);
  });
});
