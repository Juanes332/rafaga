import { http, HttpResponse, type HttpHandler } from "msw";
import { API } from "../api-base";
import { errorBody, mockId, registerReset } from "../mock-state";
import type { Report, ReportCreate } from "@/types/exports/export.types";

interface StoredReport extends Report {
  project_id: string;
}

export const reportsState = { reports: [] as StoredReport[], requests: [] as ReportCreate[] };
registerReset(() => {
  reportsState.reports = [
    {
      id: "00000000-0000-4000-8000-0000000000f1",
      project_id: "00000000-0000-4000-8000-0000000000p1",
      version: 1,
      status: "completed",
      progress: 1,
      error: null,
      created_at: "2026-11-12T16:20:00Z",
    },
  ];
  reportsState.requests = [];
});

function advance(r: StoredReport): StoredReport {
  if (r.status === "queued") return { ...r, status: "running", progress: 0.4 };
  if (r.status === "running") return { ...r, status: "completed", progress: 1 };
  return r;
}

const PDF = new TextEncoder().encode("%PDF-1.4\n%mock\n");

/** MSW handlers for the reports domain. */
export const reportsHandlers: HttpHandler[] = [
  http.get(`${API}/projects/:id/reports`, ({ params }) => {
    reportsState.reports = reportsState.reports.map((r) => (r.project_id === params.id ? advance(r) : r));
    const list = reportsState.reports.filter((r) => r.project_id === params.id).sort((a, b) => b.version - a.version);
    return HttpResponse.json(list.map(({ project_id: _p, ...r }) => r));
  }),
  http.post(`${API}/projects/:id/reports`, async ({ params, request }) => {
    const body = (await request.json()) as ReportCreate;
    reportsState.requests.push(body);
    if (body.study_ids.length === 0) return HttpResponse.json(errorBody("results_missing"), { status: 409 });
    const mine = reportsState.reports.filter((r) => r.project_id === params.id);
    const id = mockId("f");
    const version = mine.reduce((m, r) => Math.max(m, r.version), 0) + 1;
    reportsState.reports.push({ id, project_id: String(params.id), version, status: "queued", progress: 0, error: null, created_at: new Date().toISOString() });
    return HttpResponse.json({ report_id: id }, { status: 202 });
  }),
  http.get(`${API}/reports/:id/file`, ({ params }) => {
    const r = reportsState.reports.find((x) => x.id === params.id);
    if (r?.status !== "completed") return HttpResponse.json(errorBody("report_not_ready"), { status: 409 });
    return new HttpResponse(PDF, { headers: { "Content-Type": "application/pdf" } });
  }),
];
