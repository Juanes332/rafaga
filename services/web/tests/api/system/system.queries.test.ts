import { describe, expect, it } from "vitest";
import { systemStatusQueryOptions } from "@/api/system/system.queries";
import { createTestQueryClient } from "../../utils/render-with-providers";

describe("system api", () => {
  it("reads compute device and health", async () => {
    const s = await createTestQueryClient().fetchQuery(systemStatusQueryOptions());
    expect(s.solver.gpu_name).toBe("NVIDIA RTX 4060");
  });
});
