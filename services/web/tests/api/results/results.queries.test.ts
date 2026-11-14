import { describe, expect, it } from "vitest";
import { fieldQueryOptions, resultQueryOptions, viewer3dQueryOptions, zonesQueryOptions } from "@/api/results/results.queries";
import { comfortQueryOptions } from "@/api/results/comfort.queries";
import { createTestQueryClient } from "../../utils/render-with-providers";
import { R1, R3, S1 } from "../../msw/results/results.ids";

describe("results api", () => {
  it("reads result metadata with the output grid", async () => {
    const r = await createTestQueryClient().fetchQuery(resultQueryOptions(R1));
    expect(r.output_grid).toMatchObject({ frame: "plan", nx: 160, ny: 120 });
  });
  it("decodes a binary K field with its shape header", async () => {
    const f = await createTestQueryClient().fetchQuery(fieldQueryOptions(R1, "K"));
    expect([f.rows, f.cols]).toEqual([120, 160]);
    expect(f.data).toBeInstanceOf(Float32Array);
  });
  it("re-thresholds zones per settings", async () => {
    const qc = createTestQueryClient();
    const low = await qc.fetchQuery(zonesQueryOptions(R1, 1.1, 0.3));
    const high = await qc.fetchQuery(zonesQueryOptions(R1, 1.4, 0.3));
    const acc = (z: typeof low) => z.zones.find((x) => x.zone === "acceleration")?.area_m2 ?? 0;
    expect(acc(low)).toBeGreaterThan(acc(high));
  });
  it("reads the 3D viewer payload and comfort", async () => {
    const qc = createTestQueryClient();
    expect((await qc.fetchQuery(viewer3dQueryOptions(R3))).slices).toHaveLength(2);
    expect((await qc.fetchQuery(comfortQueryOptions(S1))).class_areas).toHaveLength(5);
  });
  it("rejects viewer3d for plan results with viewer_not_available", async () => {
    await expect(createTestQueryClient().fetchQuery(viewer3dQueryOptions(R1))).rejects.toMatchObject({ code: "viewer_not_available" });
  });
});
