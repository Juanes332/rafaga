import { http, HttpResponse, type HttpHandler } from "msw";
import { classifyZones, zoneAreas } from "@/engines/fields/zones";
import type { Field } from "@/engines/fields/field.decode";
import type { ZoneAreas } from "@/types/results/result.types";
import { API } from "../api-base";
import { errorBody, registerReset } from "../mock-state";
import { comfortFixture, planFields, resultFixtures, viewer3dFixture } from "./results.fixtures";
import { GRID, R3, R4, SECTION_GRID } from "./results.ids";
import { synthSection, toBuffer } from "./results.synth";

export const resultsState = { results: resultFixtures(), comfortRecomputed: 0 };
registerReset(() => {
  resultsState.results = resultFixtures();
  resultsState.comfortRecomputed = 0;
});

const notFound = (code: string) => HttpResponse.json(errorBody(code), { status: 404 });

function binary(data: Float32Array | Uint8Array, rows: number, cols: number) {
  return HttpResponse.arrayBuffer(toBuffer(data), {
    headers: { "Content-Type": "application/octet-stream", "X-Field-Shape": `${rows},${cols}`, "X-Field-Dtype": data instanceof Uint8Array ? "uint8" : "float32" },
  });
}

/** Raw field for a fixture result, or null when the result has no such field. */
export function fieldData(id: string, name: string): { data: Float32Array | Uint8Array; rows: number; cols: number } | null {
  if (id === R4) {
    const s = synthSection(SECTION_GRID.ns, SECTION_GRID.nz, SECTION_GRID.s0);
    const k = s.map((v) => v / 4.2);
    const map: Record<string, Float32Array> = { speed: s, us: s, K: k, uz: new Float32Array(s.length) };
    return map[name] ? { data: map[name], rows: SECTION_GRID.nz, cols: SECTION_GRID.ns } : null;
  }
  if (id === R3 && (name === "slice_xz" || name === "slice_yz")) {
    const cols = name === "slice_xz" ? 160 : 120;
    return { data: synthSection(cols, 60, name === "slice_xz" ? -40 : -50), rows: 60, cols };
  }
  const f = planFields(id);
  const map: Record<string, Float32Array | Uint8Array> = { K: f.K, ux: f.ux, uy: f.uy, speed: f.speed, mask: f.mask, lawson_class: f.lawson };
  if (id === R3) map.uz = new Float32Array(f.K.length);
  return map[name] ? { data: map[name], rows: GRID.ny, cols: GRID.nx } : null;
}

export function zonesFor(id: string, kAccel: number, kStag: number): ZoneAreas {
  const f = planFields(id);
  const field: Field = { rows: GRID.ny, cols: GRID.nx, dtype: "float32", data: f.K };
  const a = zoneAreas(classifyZones(field, { k_accel: kAccel, k_stagnation: kStag }), GRID.dx_m);
  return {
    result_id: id,
    thresholds: { k_accel: kAccel, k_stagnation: kStag },
    fluid_area_m2: a.fluidM2,
    zones: [
      { zone: "acceleration", ...a.acceleration },
      { zone: "stagnation", ...a.stagnation },
    ],
  };
}

/** MSW handlers for results, fields, zones, 3D viewer and comfort. */
export const resultsHandlers: HttpHandler[] = [
  http.get(`${API}/results/:id`, ({ params }) => {
    const r = resultsState.results[String(params.id)];
    return r ? HttpResponse.json(r) : notFound("result_not_found");
  }),
  http.get(`${API}/results/:id/fields/:name`, ({ params }) => {
    if (!resultsState.results[String(params.id)]) return notFound("result_not_found");
    const f = fieldData(String(params.id), String(params.name));
    return f ? binary(f.data, f.rows, f.cols) : notFound("field_not_found");
  }),
  http.get(`${API}/results/:id/zones`, ({ params, request }) => {
    const q = new URL(request.url).searchParams;
    return HttpResponse.json(zonesFor(String(params.id), Number(q.get("k_accel") ?? 1.2), Number(q.get("k_stagnation") ?? 0.3)));
  }),
  http.get(`${API}/results/:id/viewer3d`, ({ params }) =>
    params.id === R3 ? HttpResponse.json(viewer3dFixture()) : notFound("viewer_not_available"),
  ),
  http.get(`${API}/simulations/:id/comfort`, ({ params }) => HttpResponse.json(comfortFixture(String(params.id)))),
  http.post(`${API}/simulations/:id/comfort/recompute`, ({ params }) => {
    resultsState.comfortRecomputed += 1;
    return HttpResponse.json({ ...comfortFixture(String(params.id)), status: "running" }, { status: 202 });
  }),
];
