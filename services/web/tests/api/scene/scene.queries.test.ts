import { describe, expect, it } from "vitest";
import { sceneKeys, sceneQueryOptions } from "@/api/scene/scene.queries";
import { createTestQueryClient } from "../../utils/render-with-providers";

describe("scene api", () => {
  it("reads solids and porous zones of an alternative", async () => {
    const scene = await createTestQueryClient().fetchQuery(sceneQueryOptions("00000000-0000-4000-8000-0000000000c1"));
    expect(scene.solids).toHaveLength(2);
    expect(scene.porous[0].model).toBe("screen");
    expect(sceneKeys.detail("x")).toEqual(["scene", "x"]);
  });
});
