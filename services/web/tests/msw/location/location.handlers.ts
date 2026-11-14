import { http, HttpResponse, type HttpHandler } from "msw";
import { API } from "../api-base";
import { errorBody, registerReset } from "../mock-state";
import { projectsState } from "../projects/projects.handlers";
import type { LocationRequest } from "@/types/projects/project.types";

/** Toggle to simulate the elevation service being down (503 elevation_unavailable). */
export const locationState = { elevationDown: false };
registerReset(() => {
  locationState.elevationDown = false;
});

/** ISA air density at an altitude (kg/m³). */
export function isaDensity(h: number): number {
  return 1.225 * Math.pow(1 - 2.25577e-5 * h, 4.2559);
}

/** Deterministic synthetic elevation so tests never depend on a real place. */
export function syntheticElevation(lat: number, lon: number): number {
  return Math.round(Math.abs(Math.sin(lat) * 900 + Math.cos(lon) * 600));
}

/** MSW handlers for the location domain. */
export const locationHandlers: HttpHandler[] = [
  http.put(`${API}/projects/:id/location`, async ({ params, request }) => {
    const p = projectsState.projects.find((x) => x.id === params.id);
    if (!p) return HttpResponse.json(errorBody("project_not_found"), { status: 404 });
    const body = (await request.json()) as LocationRequest;
    if (Math.abs(body.lat) > 90 || Math.abs(body.lon) > 180) {
      return HttpResponse.json(errorBody("coordinates_out_of_range"), { status: 422 });
    }
    const manual = body.elevation_m !== undefined && body.elevation_m !== null;
    if (!manual && locationState.elevationDown) {
      return HttpResponse.json({ ...errorBody("elevation_unavailable"), hint: "enter elevation manually" }, { status: 503 });
    }
    const elevation = manual ? Number(body.elevation_m) : syntheticElevation(body.lat, body.lon);
    Object.assign(p, {
      lat: body.lat,
      lon: body.lon,
      elevation_m: elevation,
      elevation_source: manual ? "manual" : "open_meteo",
      air_density_kg_m3: Math.round(isaDensity(elevation) * 1000) / 1000,
      updated_at: new Date().toISOString(),
    });
    return HttpResponse.json(p);
  }),
];
