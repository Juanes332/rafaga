import { http, HttpResponse, type HttpHandler } from "msw";
import { reductionZones, zoneAreas } from "@/engines/fields/zones";
import { subtractFields } from "@/engines/fields/field.raster";
import type { ComparisonCheck } from "@/types/comparisons/comparison.types";
import { API } from "../api-base";
import { errorBody } from "../mock-state";
import { comfortFixture, planFields } from "../results/results.fixtures";
import { zonesFor, resultsState } from "../results/results.handlers";
import { GRID } from "../results/results.ids";

export function checkPair(a: string, b: string): ComparisonCheck {
  const ra = resultsState.results[a];
  const rb = resultsState.results[b];
  const differences: NonNullable<ComparisonCheck["differences"]> = [];
  if (ra.kind !== rb.kind) differences.push({ field: "kind", a: ra.kind, b: rb.kind });
  if (ra.direction_deg !== rb.direction_deg) differences.push({ field: "direction", a: ra.direction_deg, b: rb.direction_deg });
  if (ra.dx_m !== rb.dx_m) differences.push({ field: "dx", a: ra.dx_m, b: rb.dx_m });
  return { comparable: differences.length === 0, differences };
}

const field = (data: Float32Array) => ({ rows: GRID.ny, cols: GRID.nx, dtype: "float32" as const, data });

/** MSW handlers for the comparisons domain. */
export const comparisonsHandlers: HttpHandler[] = [
  http.get(`${API}/comparisons/check`, ({ request }) => {
    const q = new URL(request.url).searchParams;
    return HttpResponse.json(checkPair(String(q.get("a")), String(q.get("b"))));
  }),
  http.get(`${API}/comparisons/areas`, ({ request }) => {
    const q = new URL(request.url).searchParams;
    const a = String(q.get("a"));
    const b = String(q.get("b"));
    const check = checkPair(a, b);
    if (!check.comparable) return HttpResponse.json(errorBody("results_incomparable", "x", { differences: check.differences }), { status: 422 });
    const ka = Number(q.get("k_accel") ?? 1.2);
    const ks = Number(q.get("k_stagnation") ?? 0.3);
    const dr = Number(q.get("dk_reduction") ?? -0.1);
    const dk = subtractFields(field(planFields(a).K), field(planFields(b).K));
    const red = zoneAreas(reductionZones(dk, dr), GRID.dx_m).reduction;
    return HttpResponse.json({
      a: zonesFor(a, ka, ks),
      b: zonesFor(b, ka, ks),
      reduction: { zone: "reduction", ...red },
      thresholds: { k_accel: ka, k_stagnation: ks, dk_reduction: dr },
    });
  }),
  http.get(`${API}/comparisons/comfort`, ({ request }) => {
    const q = new URL(request.url).searchParams;
    return HttpResponse.json({ a: comfortFixture(String(q.get("study_a"))), b: comfortFixture(String(q.get("study_b"))) });
  }),
];
