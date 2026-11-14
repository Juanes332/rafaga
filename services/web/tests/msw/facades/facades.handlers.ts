import { http, HttpResponse, type HttpHandler } from "msw";
import { API } from "../api-base";
import { alternativesState, ALT_SCREEN } from "../alternatives/alternatives.handlers";
import { geometryState } from "../geometry/geometry.handlers";
import { errorBody, mockId, registerReset } from "../mock-state";
import type { Adjustment, FacadeElement, FacadeElementCreate } from "@/types/facades/facade.types";
import { STRATEGIES } from "./facades.fixtures";

export const SCREEN_ELEMENT = "00000000-0000-4000-8000-0000000000e1";
const TORRE_A = "00000000-0000-4000-8000-0000000000b1";

/** Facade elements per alternative id. */
export const facadesState = { byAlternative: {} as Record<string, FacadeElement[]> };
registerReset(() => {
  facadesState.byAlternative = {
    [ALT_SCREEN]: [
      { id: SCREEN_ELEMENT, building_id: TORRE_A, edge_index: 1, orphaned: false, type: "screen", params: { porosity: 0.4, height_m: 3, offset_m: 0.5 } },
    ],
  };
});

function buildingHeight(buildingId: string): number | null {
  for (const g of Object.values(geometryState.byProject)) {
    const b = g.buildings.find((x) => x.id === buildingId);
    if (b) return b.height_m;
  }
  return null;
}

/** Heights above the building are clamped, like the api does (FR-31). */
function clamp(buildingId: string, params: Record<string, number | null>): [Record<string, number | null>, Adjustment[]] {
  const h = buildingHeight(buildingId);
  const requested = params.height_m;
  if (h === null || requested == null || requested <= h) return [params, []];
  return [{ ...params, height_m: h }, [{ field: "height_m", requested, applied: h, reason: "clamped_to_building_height" }]];
}

function findElement(id: string): [FacadeElement[], FacadeElement] | null {
  for (const list of Object.values(facadesState.byAlternative)) {
    const el = list.find((e) => e.id === id);
    if (el) return [list, el];
  }
  return null;
}

function bumpCount(alternativeId: string, delta: number) {
  for (const list of Object.values(alternativesState.byProject)) {
    const alt = list.find((a) => a.id === alternativeId);
    if (alt) alt.element_count = (alt.element_count ?? 0) + delta;
  }
}

/** MSW handlers for the facades domain. */
export const facadesHandlers: HttpHandler[] = [
  http.get(`${API}/facade-strategies`, () => HttpResponse.json(STRATEGIES)),
  http.get(`${API}/alternatives/:id/facade-elements`, ({ params }) => HttpResponse.json(facadesState.byAlternative[String(params.id)] ?? [])),
  http.post(`${API}/alternatives/:id/facade-elements`, async ({ params, request }) => {
    const body = (await request.json()) as FacadeElementCreate;
    if (buildingHeight(body.building_id) === null) return HttpResponse.json(errorBody("edge_not_found"), { status: 422 });
    const [applied, adjustments] = clamp(body.building_id, body.params);
    const el = { id: mockId("e"), building_id: body.building_id, edge_index: body.edge_index, orphaned: false, type: body.type, params: applied } as FacadeElement;
    const key = String(params.id);
    (facadesState.byAlternative[key] ??= []).push(el);
    bumpCount(key, 1);
    return HttpResponse.json({ ...el, adjustments }, { status: 201 });
  }),
  http.patch(`${API}/facade-elements/:id`, async ({ params, request }) => {
    const found = findElement(String(params.id));
    if (!found) return HttpResponse.json(errorBody("element_not_found"), { status: 404 });
    const body = (await request.json()) as { params: Record<string, number | null> };
    const [applied, adjustments] = clamp(found[1].building_id, { ...(found[1].params as Record<string, number | null>), ...body.params });
    Object.assign(found[1], { params: applied });
    return HttpResponse.json({ ...found[1], adjustments });
  }),
  http.delete(`${API}/facade-elements/:id`, ({ params }) => {
    const found = findElement(String(params.id));
    if (!found) return HttpResponse.json(errorBody("element_not_found"), { status: 404 });
    found[0].splice(found[0].indexOf(found[1]), 1);
    for (const [altId, list] of Object.entries(facadesState.byAlternative)) if (list === found[0]) bumpCount(altId, -1);
    return new HttpResponse(null, { status: 204 });
  }),
];
