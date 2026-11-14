import { http, HttpResponse, type HttpHandler } from "msw";
import { API } from "../api-base";
import { errorBody } from "../mock-state";

/** No tile cache in mock mode: the map shows its neutral offline grid (ADR-09). */
export const tilesHandlers: HttpHandler[] = [
  http.get(`${API}/tiles/:z/:x/:y`, () => HttpResponse.json(errorBody("tile_unavailable"), { status: 503 })),
];
