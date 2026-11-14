import { http, HttpResponse, type HttpHandler } from "msw";
import { API } from "../api-base";
import { errorBody, mockId, registerReset } from "../mock-state";
import type { Alternative, AlternativeCreate, AlternativePatch } from "@/types/alternatives/alternative.types";

export const ALT_BASE = "00000000-0000-4000-8000-0000000000c0";
export const ALT_SCREEN = "00000000-0000-4000-8000-0000000000c1";
export const ALTERNATIVES_LIMIT = 8;

export function baseAlternative(): Alternative {
  return { id: ALT_BASE, name: "Base", is_base: true, position: 0, element_count: 0, latest_results_summary: null };
}

/** Alternatives per project id; every project has at least its base. */
export const alternativesState = { byProject: {} as Record<string, Alternative[]> };
registerReset(() => {
  alternativesState.byProject = {
    "00000000-0000-4000-8000-0000000000p1": [
      baseAlternative(),
      { id: ALT_SCREEN, name: "Celosía 40 %", is_base: false, position: 1, element_count: 1, latest_results_summary: null },
    ],
  };
});

export function alternativesOf(projectId: string): Alternative[] {
  alternativesState.byProject[projectId] ??= [{ ...baseAlternative(), id: `${ALT_BASE.slice(0, -2)}${projectId.slice(-2)}` }];
  return alternativesState.byProject[projectId];
}

function findAlternative(id: string): [Alternative[], Alternative] | null {
  for (const list of Object.values(alternativesState.byProject)) {
    const alt = list.find((a) => a.id === id);
    if (alt) return [list, alt];
  }
  return null;
}

const notFound = () => HttpResponse.json(errorBody("alternative_not_found"), { status: 404 });

/** MSW handlers for the alternatives domain. */
export const alternativesHandlers: HttpHandler[] = [
  http.get(`${API}/projects/:id/alternatives`, ({ params }) => HttpResponse.json(alternativesOf(String(params.id)))),
  http.post(`${API}/projects/:id/alternatives`, async ({ params, request }) => {
    const list = alternativesOf(String(params.id));
    if (list.length >= ALTERNATIVES_LIMIT) {
      return HttpResponse.json(errorBody("alternatives_limit", "limit", { limit: ALTERNATIVES_LIMIT }), { status: 409 });
    }
    const body = (await request.json()) as AlternativeCreate;
    const alt: Alternative = { id: mockId("c"), name: body.name, is_base: false, position: list.length, element_count: 0, latest_results_summary: null };
    list.push(alt);
    return HttpResponse.json(alt, { status: 201 });
  }),
  http.patch(`${API}/alternatives/:id`, async ({ params, request }) => {
    const found = findAlternative(String(params.id));
    if (!found) return notFound();
    Object.assign(found[1], (await request.json()) as AlternativePatch);
    return HttpResponse.json(found[1]);
  }),
  http.delete(`${API}/alternatives/:id`, ({ params }) => {
    const found = findAlternative(String(params.id));
    if (!found) return notFound();
    if (found[1].is_base) return HttpResponse.json(errorBody("base_undeletable"), { status: 409 });
    found[0].splice(found[0].indexOf(found[1]), 1);
    return new HttpResponse(null, { status: 204 });
  }),
];
