import type { Comfort, Result, Viewer3D } from "@/types/results/result.types";
import { GRID, P1, R1, R2, R3, R4, S1, S2, S3, S4, SECTION_GRID } from "./results.ids";
import { synthPlan, type PlanFields } from "./results.synth";

const KEY = "a3b2a89cef7058f386a9d72ebcf4dbb86fc125b86a2336e7842f82d137f90cee";

function plan(id: string, study: string, over: Partial<Result> = {}): Result {
  return {
    id,
    job_id: id.replace("r", "j"),
    study_id: study,
    kind: "plan2d",
    direction_deg: 90,
    device: "gpu",
    dx_m: 1,
    output_grid: GRID,
    stats: { k_mean: 0.74, k_max: 1.63, k_p95: 1.21 },
    convergence: { converged: true, flow_throughs: 3.25, rel_change: 0.007 },
    fields: ["K", "ux", "uy", "speed", "mask"],
    images: ["k", "speed", "zones"],
    comparability_key: KEY,
    warnings: [],
    created_at: "2026-11-13T09:30:00Z",
    ...over,
  };
}

export function resultFixtures(): Record<string, Result> {
  return {
    [R1]: plan(R1, S1),
    [R2]: plan(R2, S2, { stats: { k_mean: 0.66, k_max: 1.48, k_p95: 1.09 }, warnings: ["element_not_representable_2d", "future_code"] }),
    [R3]: plan(R3, S3, { kind: "volume3d", fields: ["K", "ux", "uy", "uz", "speed", "mask", "ti"], comparability_key: "volume" }),
    [R4]: plan(R4, S4, { kind: "section2d", output_grid: SECTION_GRID, fields: ["K", "us", "uz", "speed", "mask"], comparability_key: "section" }),
  };
}

/** Plan fields are deterministic and costly enough to build once. */
const cache = new Map<boolean, PlanFields>();
export function planFields(resultId: string): PlanFields {
  const calmer = resultId === R2;
  if (!cache.has(calmer)) cache.set(calmer, synthPlan(calmer));
  return cache.get(calmer) as PlanFields;
}

export function comfortFixture(studyId: string): Comfort {
  const calmer = studyId === S2;
  return {
    study_id: studyId,
    status: "completed",
    lawson_hash: "lawson-default",
    coverage: 0.97,
    partial: false,
    class_areas: [
      { class: "A", area_m2: calmer ? 6120 : 5480, percent: calmer ? 34.1 : 30.5 },
      { class: "B", area_m2: calmer ? 6010 : 5600, percent: calmer ? 33.5 : 31.2 },
      { class: "C", area_m2: calmer ? 3900 : 4150, percent: calmer ? 21.7 : 23.1 },
      { class: "D", area_m2: calmer ? 1620 : 2010, percent: calmer ? 9 : 11.2 },
      { class: "E", area_m2: calmer ? 300 : 710, percent: calmer ? 1.7 : 4 },
    ],
    safety_areas: [
      { class: "S15", area_m2: calmer ? 0 : 42, percent: calmer ? 0 : 0.2 },
      { class: "S20", area_m2: 0, percent: 0 },
    ],
    image: "lawson",
    field: "lawson_class",
  };
}

/** Prism scene + vertical slices + streamlines for the 3D viewer (r3). */
export function viewer3dFixture(): Viewer3D {
  const prism = (id: string, fp: number[][], h: number) => ({ id, origin: "building", footprint: fp, holes: [], z_min: 0, z_max: h });
  const lines = Array.from({ length: 24 }, (_, i) => {
    const y = -30 + i * 3.2;
    const z = 1.5 + (i % 6) * 6;
    return Array.from({ length: 60 }, (_, k) => {
      const x = 110 - k * 2.5;
      const bump = x > -2 && x < 32 && y > -4 && y < 24 ? 8 * Math.sin(((x + 2) / 34) * Math.PI) : 0;
      return [x, y + Math.sin(k / 9) * 1.5, z + bump];
    });
  });
  return {
    scene: {
      schema_version: "1.0",
      units: "m",
      frame: "local_enu",
      source: { project_id: P1, alternative_id: "00000000-0000-4000-8000-0000000000c0", geometry_version: 3, compiled_at: "2026-11-13T09:00:00Z" },
      analysis_height_m: 1.5,
      ground: { z0_m: 0.5 },
      h_max_m: 36,
      bounds: { base_min: [0, -5, 0], base_max: [70, 20, 36], envelope_m: 10 },
      solids: [
        prism("00000000-0000-4000-8000-0000000000b1", [[0, 0], [30, 0], [30, 20], [0, 20]], 36),
        prism("00000000-0000-4000-8000-0000000000b2", [[45, -5], [70, -5], [70, 12], [45, 12]], 18),
      ],
      porous: [],
      warnings: [],
    } as unknown as Viewer3D["scene"],
    slices: [
      { name: "xz", plane: "xz", extents: [-40, 120, 0, 60], field: "slice_xz", shape: [60, 160] },
      { name: "yz", plane: "yz", extents: [-50, 70, 0, 60], field: "slice_yz", shape: [60, 120] },
    ],
    streamlines: lines,
  };
}
