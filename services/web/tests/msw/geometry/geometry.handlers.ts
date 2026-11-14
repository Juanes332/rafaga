import { http, HttpResponse, type HttpHandler } from "msw";
import { API } from "../api-base";
import { errorBody, registerReset } from "../mock-state";
import { alternativesOf } from "../alternatives/alternatives.handlers";
import type { Building, Geometry, GeometryIssue, ImportReport } from "@/types/geometry/geometry.types";

export const P1 = "00000000-0000-4000-8000-0000000000p1";

/** Two blocks in local ENU metres (CCW footprints). */
export function sampleBuildings(): Building[] {
  return [
    { id: "00000000-0000-4000-8000-0000000000b1", name: "Torre A", footprint: [[0, 0], [30, 0], [30, 20], [0, 20]], height_m: 36, holes: [], source: "draw", missing_height: false },
    { id: "00000000-0000-4000-8000-0000000000b2", name: "Bloque B", footprint: [[45, -5], [70, -5], [70, 12], [45, 12]], height_m: 18, holes: [], source: "draw", missing_height: false },
  ];
}

/** Geometry per project id; projects without an entry have version 1 and no buildings. */
export const geometryState = { byProject: {} as Record<string, Geometry> };
registerReset(() => {
  geometryState.byProject = { [P1]: { version: 3, buildings: sampleBuildings(), issues: [] } };
});

export function geometryOf(projectId: string): Geometry {
  return geometryState.byProject[projectId] ?? { version: 1, buildings: [], issues: [] };
}

function issuesFor(buildings: Building[]): GeometryIssue[] {
  return buildings.flatMap((b): GeometryIssue[] => {
    if (b.height_m == null) return [{ building_id: b.id, code: "missing_height", message_key: "geometry.missing_height", location: null }];
    if (b.height_m < 1 || b.height_m > 500) return [{ building_id: b.id, code: "height_out_of_range", message_key: "geometry.height_out_of_range", location: null }];
    return [];
  });
}

type PutBody = { expected_version: number; confirm_base_change?: boolean; buildings: Building[] };

const importedBuildings = (): Building[] => [
  { id: "00000000-0000-4000-8000-0000000000i1", name: "Importado 1", footprint: [[0, 40], [20, 40], [20, 55], [0, 55]], height_m: 15, holes: [], source: "dxf", missing_height: false },
  { id: "00000000-0000-4000-8000-0000000000i2", name: "Importado 2", footprint: [[30, 40], [42, 40], [42, 52], [30, 52]], height_m: null, holes: [], source: "dxf", missing_height: true },
];

function importReport(projectId: string, fileName: string): ImportReport | null {
  if (fileName.startsWith("falla")) return null;
  const current = geometryOf(projectId);
  const added = importedBuildings();
  const geometry = { version: current.version + 1, buildings: [...current.buildings, ...added], issues: issuesFor(added) };
  geometryState.byProject[projectId] = geometry;
  return {
    buildings_added: 2,
    missing_height: [added[1].id],
    ignored: [{ entity: "TEXT", reason: "text_not_geometry" }, { entity: "LWPOLYLINE (abierta)", reason: "open_polyline" }],
    detected_unit: "cm",
    warnings: [],
    geometry,
  };
}

/** MSW handlers for the geometry domain. */
export const geometryHandlers: HttpHandler[] = [
  http.get(`${API}/projects/:id/geometry`, ({ params }) => HttpResponse.json(geometryOf(String(params.id)))),
  http.put(`${API}/projects/:id/geometry`, async ({ params, request }) => {
    const id = String(params.id);
    const body = (await request.json()) as PutBody;
    const current = geometryOf(id);
    if (body.expected_version !== current.version) return HttpResponse.json(errorBody("version_conflict"), { status: 409 });
    if (alternativesOf(id).length > 1 && !body.confirm_base_change) return HttpResponse.json(errorBody("base_locked"), { status: 409 });
    const next = { version: current.version + 1, buildings: body.buildings, issues: issuesFor(body.buildings), orphaned_elements: [] };
    geometryState.byProject[id] = next;
    return HttpResponse.json(next);
  }),
  http.post(`${API}/projects/:id/geometry/validate`, async ({ request }) => {
    const body = (await request.json()) as { buildings: Building[] };
    return HttpResponse.json({ issues: issuesFor(body.buildings) });
  }),
  http.post(`${API}/projects/:id/geometry/imports`, async ({ params, request }) => {
    const file = (await request.formData()).get("file") as File;
    // WP-API: imports have no confirm flag; they are refused while alternatives exist.
    if (alternativesOf(String(params.id)).length > 1) return HttpResponse.json(errorBody("base_locked"), { status: 409 });
    const report = importReport(String(params.id), file.name);
    if (!report) {
      return HttpResponse.json(errorBody("import_failed", "no closed polylines", { hint_key: "dxf_not_closed" }), { status: 422 });
    }
    return HttpResponse.json(report, { status: 201 });
  }),
];
