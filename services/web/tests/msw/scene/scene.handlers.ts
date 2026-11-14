import { http, HttpResponse, type HttpHandler } from "msw";
import { API } from "../api-base";
import { geometryOf, P1 } from "../geometry/geometry.handlers";
import type { ScenePorous, SceneView } from "@/types/scene/scene-view.types";

function screenPrism(buildingId: string): ScenePorous {
  const extra = { porosity: 0.4, loss_coefficient: 8.23, normal: [0, -1], thickness_m: 0.1 };
  return {
    id: "f:screen-1:0",
    origin: { kind: "screen", building_id: buildingId, element_id: "screen-1" },
    footprint: [[0, -0.6], [30, -0.6], [30, -0.5], [0, -0.5]],
    z_min: 0,
    z_max: 3,
    model: "screen",
    ...extra,
  };
}

/** Compile a scene from the mock geometry; the screen alternative gets one porous screen. */
export function mockScene(alternativeId: string, projectId = P1): SceneView & Record<string, unknown> {
  const { buildings, version } = geometryOf(projectId);
  const hMax = Math.max(1, ...buildings.map((b) => b.height_m ?? 0));
  const withScreen = alternativeId.endsWith("c1");
  return {
    schema_version: "1.0",
    units: "m",
    frame: "local_enu",
    source: { project_id: projectId, alternative_id: alternativeId, geometry_version: version, compiled_at: "2026-11-13T12:00:00Z" },
    analysis_height_m: 1.5,
    ground: { z0_m: 0.5 },
    h_max_m: hMax,
    bounds: { base_min: [0, -5, 0], base_max: [70, 20, hMax], envelope_m: 10 },
    solids: buildings.map((b) => ({
      id: `b:${b.id}:t0`,
      origin: { kind: "building", building_id: b.id, element_id: null },
      footprint: b.footprint,
      holes: [],
      z_min: 0,
      z_max: b.height_m ?? 1,
      thin_axis_m: null,
    })),
    porous: withScreen ? [screenPrism(buildings[0]?.id ?? "")] : [],
    warnings: [],
  };
}

/** MSW handlers for the scene domain. */
export const sceneHandlers: HttpHandler[] = [
  http.get(`${API}/alternatives/:id/scene`, ({ params }) => HttpResponse.json(mockScene(String(params.id)))),
];
