import type { Estimate, EstimateRequest, Job, Study } from "@/types/simulations/simulation.types";

export const P1 = "00000000-0000-4000-8000-0000000000p1";
export const S1 = "00000000-0000-4000-8000-0000000000s1";
export const S2 = "00000000-0000-4000-8000-0000000000s2";
export const S3 = "00000000-0000-4000-8000-0000000000s3";
export const R1 = "00000000-0000-4000-8000-0000000000r1";
export const R2 = "00000000-0000-4000-8000-0000000000r2";
export const FAILED_JOB = "00000000-0000-4000-8000-0000000000j5";

export function job(over: Partial<Job> & Pick<Job, "id">): Job {
  return {
    study_id: null,
    kind: "plan2d",
    lane: "heavy",
    direction_deg: 90,
    status: "queued",
    progress: 0,
    phase: null,
    eta_seconds: null,
    device_used: null,
    resumable: false,
    cancel_requested: false,
    error: null,
    result_id: null,
    created_at: "2026-11-13T09:00:00Z",
    started_at: null,
    finished_at: null,
    ...over,
  };
}

function completedStudy(id: string, alternativeId: string, name: string, resultId: string): Study {
  return {
    id,
    project_id: P1,
    alternative_id: alternativeId,
    alternative_name: name,
    kind: "plan2d",
    directions_deg: [90],
    section: null,
    dx_m: 1,
    device: "auto",
    status: "completed",
    progress: 1,
    coverage: 0.2,
    created_at: "2026-11-13T08:00:00Z",
    jobs: [job({ id: `${id.slice(0, -2)}j${id.slice(-1)}`, study_id: id, status: "completed", progress: 1, device_used: "gpu", result_id: resultId, phase: "done" })],
  };
}

export function seedStudies(altBase: string, altScreen: string): Study[] {
  const running: Study = {
    ...completedStudy(S3, altScreen, "Celosía 40 %", ""),
    kind: "plan2d",
    directions_deg: [67.5, 90, 112.5],
    status: "running",
    progress: 0.3,
    created_at: "2026-11-13T11:40:00Z",
    jobs: [
      job({ id: "00000000-0000-4000-8000-0000000000j3", study_id: S3, direction_deg: 90, status: "running", progress: 0.42, phase: "averaging", eta_seconds: 95, device_used: "gpu" }),
      job({ id: "00000000-0000-4000-8000-0000000000j4", study_id: S3, direction_deg: 67.5, status: "queued" }),
      job({ id: FAILED_JOB, study_id: S3, direction_deg: 112.5, status: "failed", progress: 0.61, resumable: true, error: { code: "worker_restarted", message: "worker restarted", hint: null } }),
    ],
  };
  return [running, completedStudy(S2, altScreen, "Celosía 40 %", R2), completedStudy(S1, altBase, "Base", R1)];
}

const BYTES = { plan2d: 104, section2d: 104, volume3d: 224 } as const;
const GPU_BUDGET = 0.85 * 8_589_934_592 - 536_870_912;

/** Rough ADR-10 estimate over a fixed synthetic domain (240 × 180 m, 6H high). */
export function estimateFor(req: EstimateRequest): Estimate {
  const dx = req.dx_m;
  const nodes = req.kind === "volume3d" ? Math.round((240 / dx) * (180 / dx) * (216 / dx)) : Math.round((240 / dx) * (180 / dx) * 4);
  const memory = nodes * BYTES[req.kind] + 536_870_912;
  const fits = memory <= GPU_BUDGET;
  const dim = req.kind === "volume3d" ? 3 : 2;
  const proposed = fits ? null : Math.ceil(dx * Math.pow(memory / GPU_BUDGET, 1 / dim) * 4) / 4;
  const dirs = Math.max(1, req.directions_deg?.length ?? 1);
  // CPU is ~137x slower than GPU (6.4 vs 879 MLUPS measured in the solver README)
  const device = req.device === "cpu" ? "cpu" : "gpu";
  const eta = Math.ceil((nodes * dirs) / 9_000) * (device === "cpu" ? 137 : 1);
  return { device, nodes, memory_bytes: memory, budget_bytes: Math.round(GPU_BUDGET), fits, proposed_dx_m: proposed, rejected_reason: null, eta_seconds: eta };
}
