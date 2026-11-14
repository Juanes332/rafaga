import { describe, expect, it } from "vitest";
import { enuToThree, frameCamera, northRotationDeg, toMeshSpecs } from "@/components/geometry/Geometry3DView/Geometry3DView.utils";
import type { SceneView } from "@/types/scene/scene-view.types";
import type { Building } from "@/types/geometry/geometry.types";

const draft: Building[] = [{ id: "b1", footprint: [[0, 0], [10, 0], [10, 10], [0, 10]], holes: [], height_m: 24, source: "draw", missing_height: false }];
const scene: SceneView = {
  schema_version: "1.0",
  h_max_m: 20,
  analysis_height_m: 1.5,
  solids: [
    { id: "b:b1:t0", origin: { kind: "building", building_id: "b1", element_id: null }, footprint: draft[0].footprint, z_min: 0, z_max: 20 },
    { id: "f:c:0", origin: { kind: "canopy", building_id: "b1", element_id: "c" }, footprint: [[0, 10], [10, 10], [10, 12], [0, 12]], z_min: 3.5, z_max: 3.8 },
  ],
  porous: [{ id: "f:s:0", origin: { kind: "screen", building_id: "b1", element_id: "s" }, footprint: [[0, -1], [10, -1], [10, -0.9], [0, -0.9]], z_min: 0, z_max: 3, model: "screen" }],
  warnings: [],
};

describe("scene → meshes", () => {
  it("uses draft buildings so a height change shows before saving", () => {
    const specs = toMeshSpecs(draft, scene);
    const building = specs.find((s) => s.kind === "building");
    expect(building?.zMax).toBe(24);
    expect(specs.filter((s) => s.kind === "building")).toHaveLength(1);
  });
  it("keeps façade solids opaque and porous zones translucent", () => {
    const specs = toMeshSpecs(draft, scene);
    expect(specs.find((s) => s.kind === "element")).toMatchObject({ zMin: 3.5, opacity: 1 });
    const porous = specs.find((s) => s.kind === "porous");
    expect(porous?.opacity).toBeLessThan(0.6);
  });
  it("works without a scene", () => {
    expect(toMeshSpecs(draft, undefined)).toHaveLength(1);
  });
  it("maps ENU (x east, y north, z up) to three.js (y up, −z north)", () => {
    expect(enuToThree([1, 2, 3])).toEqual([1, 3, -2]);
  });
  it("frames the camera around the content", () => {
    const cam = frameCamera(toMeshSpecs(draft, scene));
    expect(cam.target).toEqual([5, 12, -5.5]);
    expect(cam.distance).toBeGreaterThan(20);
  });
});

describe("northRotationDeg", () => {
  // North is −z in three.js; OrbitControls azimuth is 0 on the +z axis and grows toward +x.
  it("puts north at the top when the camera sits south of the scene", () => {
    expect(northRotationDeg(0)).toBeCloseTo(0);
  });
  it("turns north clockwise from the top as the camera moves east", () => {
    expect(northRotationDeg(Math.PI / 4)).toBeCloseTo(45);
    expect(northRotationDeg(Math.PI / 2)).toBeCloseTo(90);
  });
  it("normalises to 0..360", () => {
    expect(northRotationDeg(-Math.PI / 2)).toBeCloseTo(270);
  });
});
