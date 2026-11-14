import { http, HttpResponse, type HttpHandler } from "msw";
import { ALT_BASE, ALT_SCREEN, alternativesState } from "../alternatives/alternatives.handlers";
import { API } from "../api-base";
import { errorBody, mockId, registerReset } from "../mock-state";
import type { EstimateRequest, Job, SimulationCreate, Study, StudySummary } from "@/types/simulations/simulation.types";
import { estimateFor, job, seedStudies } from "./simulations.fixtures";

/** Studies of every project; s3 advances on each GET so progress is visible in mock mode. */
export const simulationsState = { studies: [] as Study[], solverOffline: false };
registerReset(() => {
  simulationsState.studies = seedStudies(ALT_BASE, ALT_SCREEN);
  simulationsState.solverOffline = false;
});

function summary(s: Study): StudySummary {
  return {
    id: s.id,
    alternative_name: s.alternative_name ?? "",
    kind: s.kind,
    directions_deg: s.directions_deg ?? [],
    status: s.status,
    progress: s.progress,
    device: s.device ?? "auto",
    created_at: s.created_at ?? "",
  };
}

function advance(s: Study): void {
  const running = s.jobs.find((j) => j.status === "running");
  if (!running) return;
  running.progress = Math.min(1, running.progress + 0.04);
  running.eta_seconds = Math.max(0, Math.round((1 - running.progress) * 160));
  running.phase = running.progress < 0.3 ? "spin_up" : "averaging";
  s.progress = s.jobs.reduce((a, j) => a + j.progress, 0) / s.jobs.length;
}

function findJob(id: string): [Study, Job] | null {
  for (const s of simulationsState.studies) {
    const j = s.jobs.find((x) => x.id === id);
    if (j) return [s, j];
  }
  return null;
}

function altName(id: string): string {
  return Object.values(alternativesState.byProject).flat().find((a) => a.id === id)?.name ?? "";
}

function projectOfAlternative(id: string): string | undefined {
  return Object.entries(alternativesState.byProject).find(([, list]) => list.some((a) => a.id === id))?.[0];
}

const studyNotFound = () => HttpResponse.json(errorBody("study_not_found"), { status: 404 });

/** MSW handlers for the simulations domain. */
export const simulationsHandlers: HttpHandler[] = [
  http.get(`${API}/projects/:id/simulations`, ({ params }) =>
    HttpResponse.json(simulationsState.studies.filter((s) => s.project_id === params.id).map(summary)),
  ),
  http.post(`${API}/simulations/estimate`, async ({ request }) => {
    const estimate = estimateFor((await request.json()) as EstimateRequest);
    return HttpResponse.json(simulationsState.solverOffline ? { ...estimate, fits: false, budget_bytes: 0, rejected_reason: "solver_offline" } : estimate);
  }),
  http.post(`${API}/simulations`, async ({ request }) => {
    const body = (await request.json()) as SimulationCreate;
    const est = estimateFor(body);
    if (!est.fits && !body.auto_coarsen) {
      return HttpResponse.json(errorBody("mesh_too_large", "mesh", { proposed_dx_m: est.proposed_dx_m }), { status: 422 });
    }
    const id = mockId("s");
    const dirs = body.kind === "section2d" ? [0] : (body.directions_deg ?? [0]);
    const jobs = dirs.map((d) => job({ id: mockId("j"), study_id: id, kind: body.kind, direction_deg: d }));
    const study: Study = {
      id,
      project_id: projectOfAlternative(body.alternative_id),
      alternative_id: body.alternative_id,
      alternative_name: altName(body.alternative_id),
      kind: body.kind,
      directions_deg: dirs,
      section: body.section ?? null,
      dx_m: est.proposed_dx_m && body.auto_coarsen ? est.proposed_dx_m : body.dx_m,
      device: body.device ?? "auto",
      status: "queued",
      progress: 0,
      coverage: null,
      created_at: new Date().toISOString(),
      jobs,
    };
    jobs[0].status = "running";
    simulationsState.studies.unshift(study);
    return HttpResponse.json(study, { status: 202 });
  }),
  http.get(`${API}/simulations/:id`, ({ params }) => {
    const s = simulationsState.studies.find((x) => x.id === params.id);
    if (!s) return studyNotFound();
    advance(s);
    return HttpResponse.json(s);
  }),
  http.post(`${API}/simulations/:id/cancel`, ({ params }) => {
    const s = simulationsState.studies.find((x) => x.id === params.id);
    if (!s) return studyNotFound();
    for (const j of s.jobs) if (j.status === "queued" || j.status === "running") j.status = "cancelled";
    s.status = "cancelled";
    return HttpResponse.json(s, { status: 202 });
  }),
  http.post(`${API}/jobs/:id/cancel`, ({ params }) => {
    const found = findJob(String(params.id));
    if (!found) return HttpResponse.json(errorBody("job_not_found"), { status: 404 });
    const [, j] = found;
    if (j.status !== "queued" && j.status !== "running") return HttpResponse.json(errorBody("job_not_cancellable"), { status: 409 });
    j.status = "cancelled";
    return HttpResponse.json(j, { status: 202 });
  }),
  http.post(`${API}/jobs/:id/retry`, ({ params }) => {
    const found = findJob(String(params.id));
    if (!found) return HttpResponse.json(errorBody("job_not_found"), { status: 404 });
    const [s, j] = found;
    if (j.status !== "failed" || !j.resumable) return HttpResponse.json(errorBody("job_not_retryable"), { status: 409 });
    Object.assign(j, { status: "queued", error: null, resumable: false });
    s.status = "running";
    return HttpResponse.json(j, { status: 202 });
  }),
];
