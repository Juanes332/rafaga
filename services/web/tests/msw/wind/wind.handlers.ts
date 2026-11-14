import { http, HttpResponse, type HttpHandler } from "msw";
import { API } from "../api-base";
import { errorBody, registerReset } from "../mock-state";
import { projectsState } from "../projects/projects.handlers";
import type { WindClimate, WindPatch } from "@/types/wind/wind.types";
import { TERRAIN, eraClimate } from "./wind.fixtures";

const P1 = "00000000-0000-4000-8000-0000000000p1";

/** Wind climate per project id; missing → 404 (no climate yet). */
export const windState = { byProject: {} as Record<string, WindClimate>, era5Offline: false };
registerReset(() => {
  windState.byProject = { [P1]: eraClimate() };
  windState.era5Offline = false;
});

function projectOf(id: string) {
  return projectsState.projects.find((p) => p.id === id);
}

function manualClimate(): WindClimate {
  return { ...eraClimate(), source: "manual", rose: null, fetched_at: null, manual_direction_deg: 90, manual_u10_ms: 5 };
}

/** MSW handlers for the wind domain. */
export const windHandlers: HttpHandler[] = [
  http.get(`${API}/terrain-categories`, () => HttpResponse.json(TERRAIN)),
  http.get(`${API}/projects/:id/wind`, ({ params }) => {
    const w = windState.byProject[String(params.id)];
    return w ? HttpResponse.json(w) : HttpResponse.json(errorBody("rose_missing"), { status: 404 });
  }),
  http.post(`${API}/projects/:id/wind/era5`, ({ params }) => {
    const p = projectOf(String(params.id));
    if (!p || p.lat === null) return HttpResponse.json(errorBody("location_missing"), { status: 409 });
    if (windState.era5Offline) return HttpResponse.json(errorBody("era5_unavailable"), { status: 503 });
    windState.byProject[p.id] = { ...eraClimate(), air_density_kg_m3: p.air_density_kg_m3 ?? 1.2 };
    return HttpResponse.json(windState.byProject[p.id]);
  }),
  http.patch(`${API}/projects/:id/wind`, async ({ params, request }) => {
    const id = String(params.id);
    const patch = (await request.json()) as WindPatch;
    const current = windState.byProject[id] ?? manualClimate();
    if (patch.source === "era5" && !current.rose) return HttpResponse.json(errorBody("rose_missing"), { status: 409 });
    const terrain = TERRAIN.find((t) => t.key === patch.terrain_category);
    windState.byProject[id] = { ...current, ...patch, z0_m: patch.z0_m ?? terrain?.z0_m ?? current.z0_m };
    return HttpResponse.json(windState.byProject[id]);
  }),
];
