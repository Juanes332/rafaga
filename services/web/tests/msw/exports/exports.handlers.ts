import { http, HttpResponse, type HttpHandler } from "msw";
import { API } from "../api-base";
import { errorBody, mockId, registerReset } from "../mock-state";
import type { Export, ExportCreate } from "@/types/exports/export.types";

/** Each GET advances one step: queued → running → completed, like the light lane would. */
export const exportsState = { exports: {} as Record<string, Export>, requests: [] as ExportCreate[] };
registerReset(() => {
  exportsState.exports = {};
  exportsState.requests = [];
});

function advance(e: Export): Export {
  if (e.status === "queued") return { ...e, status: "running", progress: 0.5 };
  if (e.status === "running") return { ...e, status: "completed", progress: 1, file_ready: true };
  return e;
}

// 1×1 transparent PNG.
const PNG = Uint8Array.from(atob("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="), (c) => c.charCodeAt(0));

/** MSW handlers for the exports domain. */
export const exportsHandlers: HttpHandler[] = [
  http.post(`${API}/exports`, async ({ request }) => {
    const body = (await request.json()) as ExportCreate;
    exportsState.requests.push(body);
    if (body.layer === "delta_k" && !body.compare_result_id) {
      return HttpResponse.json(errorBody("results_incomparable"), { status: 422 });
    }
    const id = mockId("e");
    exportsState.exports[id] = { id, status: "queued", progress: 0, error: null, file_ready: false };
    return HttpResponse.json({ export_id: id }, { status: 202 });
  }),
  http.get(`${API}/exports/:id`, ({ params }) => {
    const e = exportsState.exports[String(params.id)];
    if (!e) return HttpResponse.json(errorBody("export_not_found"), { status: 404 });
    exportsState.exports[e.id] = advance(e);
    return HttpResponse.json(exportsState.exports[e.id]);
  }),
  http.get(`${API}/exports/:id/file`, ({ params }) => {
    const e = exportsState.exports[String(params.id)];
    if (!e?.file_ready) return HttpResponse.json(errorBody("export_not_ready"), { status: 409 });
    return new HttpResponse(PNG, { headers: { "Content-Type": "image/png" } });
  }),
];
