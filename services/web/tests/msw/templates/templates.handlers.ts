import { http, HttpResponse, type HttpHandler } from "msw";
import { API } from "../api-base";
import { errorBody, mockId, registerReset } from "../mock-state";
import type { Template, TemplateCreate } from "@/types/settings/settings.types";
import type { WindClimate } from "@/types/wind/wind.types";

const LOCATION_KEYS = ["lat", "lon", "latitude", "longitude", "elevation", "location"];

export const templatesState = { templates: [] as Template[], created: [] as TemplateCreate[], applied: [] as string[] };
registerReset(() => {
  templatesState.templates = [{ id: "00000000-0000-4000-8000-0000000000t1", name: "Centro urbano denso", created_at: "2026-11-09T12:00:00Z" }];
  templatesState.created = [];
  templatesState.applied = [];
});

const appliedWind: WindClimate = { source: "manual", rose: null, terrain_category: "dense_urban", z0_m: 2, from_cache: false, period_years: 10 };

/** MSW handlers for the templates domain. */
export const templatesHandlers: HttpHandler[] = [
  http.get(`${API}/templates`, () => HttpResponse.json(templatesState.templates)),
  http.post(`${API}/templates`, async ({ request }) => {
    const body = (await request.json()) as TemplateCreate;
    if (Object.keys(body.payload).some((k) => LOCATION_KEYS.includes(k))) {
      return HttpResponse.json(errorBody("template_contains_location"), { status: 422 });
    }
    templatesState.created.push(body);
    const t: Template = { id: mockId("t"), name: body.name, created_at: new Date().toISOString() };
    templatesState.templates.push(t);
    return HttpResponse.json(t, { status: 201 });
  }),
  http.delete(`${API}/templates/:id`, ({ params }) => {
    templatesState.templates = templatesState.templates.filter((t) => t.id !== params.id);
    return new HttpResponse(null, { status: 204 });
  }),
  http.post(`${API}/projects/:id/apply-template`, async ({ params, request }) => {
    const { template_id } = (await request.json()) as { template_id: string };
    if (!templatesState.templates.some((t) => t.id === template_id)) return HttpResponse.json(errorBody("template_not_found"), { status: 404 });
    templatesState.applied.push(`${String(params.id)}:${template_id}`);
    return HttpResponse.json(appliedWind);
  }),
];
