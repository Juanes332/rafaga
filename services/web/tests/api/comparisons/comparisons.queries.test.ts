import { describe, expect, it } from "vitest";
import { comparisonAreasQueryOptions, comparisonCheckQueryOptions } from "@/api/comparisons/comparisons.queries";
import { createTestQueryClient } from "../../utils/render-with-providers";
import { R1, R2, R4 } from "../../msw/results/results.ids";

const T = { k_accel: 1.2, k_stagnation: 0.3, dk_reduction: -0.1 };

describe("comparisons api", () => {
  it("reports comparable results", async () => {
    await expect(createTestQueryClient().fetchQuery(comparisonCheckQueryOptions(R1, R2))).resolves.toMatchObject({ comparable: true });
  });
  it("lists differences for incomparable results", async () => {
    const c = await createTestQueryClient().fetchQuery(comparisonCheckQueryOptions(R1, R4));
    expect(c.differences?.map((d) => d.field)).toContain("kind");
  });
  it("returns a reduction zone where the alternative is calmer", async () => {
    const a = await createTestQueryClient().fetchQuery(comparisonAreasQueryOptions(R1, R2, T));
    expect(a.reduction.area_m2).toBeGreaterThan(50);
  });
  it("fails with results_incomparable on 422", async () => {
    await expect(createTestQueryClient().fetchQuery(comparisonAreasQueryOptions(R1, R4, T))).rejects.toMatchObject({ status: 422, code: "results_incomparable" });
  });
});
