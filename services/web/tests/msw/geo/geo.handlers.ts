import { http, HttpResponse, type HttpHandler } from "msw";
import { API } from "../api-base";
import { errorBody, registerReset } from "../mock-state";
import type { GeoResult } from "@/types/geo/geo.types";

// Synthetic places: invented names and coordinates (BR-18: no real preset location).
export const PLACES: GeoResult[] = [
  { name: "Villa Sintética", admin1: "Región Uno", country: "Pruebalandia", lat: 10.12345, lon: -70.54321, elevation_m: 812 },
  { name: "Villa Sintética del Norte", admin1: "Región Dos", country: "Pruebalandia", lat: 11.5, lon: -71.25, elevation_m: 40 },
  { name: "Puerto Ficticio", admin1: null, country: "Pruebalandia", lat: -3.75, lon: 20.5, elevation_m: 3 },
];

export const geoState = { offline: false };
registerReset(() => {
  geoState.offline = false;
});

/** MSW handlers for the geo domain. */
export const geoHandlers: HttpHandler[] = [
  http.get(`${API}/geo/search`, ({ request }) => {
    if (geoState.offline) return HttpResponse.json(errorBody("geocoding_unavailable"), { status: 503 });
    const q = (new URL(request.url).searchParams.get("q") ?? "").toLowerCase();
    return HttpResponse.json(PLACES.filter((p) => p.name.toLowerCase().includes(q)));
  }),
];
