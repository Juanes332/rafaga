import { describe, expect, it } from "vitest";
import { ParticleRenderer } from "@/engines/particles/particle-gl";
import { buildVelocityData } from "@/engines/particles/particles.math";

describe("ParticleRenderer", () => {
  it("returns null without WebGL2 so the view falls back to static streamlines", () => {
    const canvas = document.createElement("canvas");
    const data = buildVelocityData(new Float32Array([1]), new Float32Array([1]), new Float32Array([0]), 1, 1);
    expect(ParticleRenderer.create(canvas, data, 1, 1, 128)).toBeNull();
  });
});
