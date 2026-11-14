import { http, HttpResponse } from "msw";
import type { Study } from "@/types/simulations/simulation.types";
import { API } from "../api-base";
import { P1, R1, R2, R3, R4, S1, S2, S3, S4 } from "./results.ids";

const ALT_BASE = "00000000-0000-4000-8000-0000000000c0";
const ALT_SCREEN = "00000000-0000-4000-8000-0000000000c1";

function study(id: string, alt: string, name: string, kind: Study["kind"], results: Array<[string, number]>): Study {
  return {
    id,
    project_id: P1,
    alternative_id: alt,
    alternative_name: name,
    kind,
    directions_deg: results.map(([, d]) => d),
    section: null,
    dx_m: 1,
    device: "auto",
    status: "completed",
    progress: 1,
    coverage: 0.97,
    created_at: "2026-11-13T09:00:00Z",
    jobs: results.map(([rid, d]) => ({
      id: rid.replace("r", "j"),
      study_id: id,
      kind,
      lane: "heavy",
      direction_deg: d,
      status: "completed",
      progress: 1,
      phase: null,
      eta_seconds: null,
      device_used: "gpu",
      resumable: false,
      cancel_requested: false,
      error: null,
      result_id: rid,
      created_at: "2026-11-13T09:00:00Z",
      started_at: null,
      finished_at: null,
    })),
  };
}

/** Studies backing the result fixtures; tests install them so they do not depend on another domain's fixtures. */
export function resultStudies(): Study[] {
  return [
    study(S1, ALT_BASE, "Base", "plan2d", [[R1, 90]]),
    study(S2, ALT_SCREEN, "Celosía 40 %", "plan2d", [[R2, 90]]),
    study(S3, ALT_BASE, "Base", "volume3d", [[R3, 90]]),
    study(S4, ALT_BASE, "Base", "section2d", [[R4, 90]]),
  ];
}

export function studyHandlers(studies: Study[] = resultStudies()) {
  return [
    http.get(`${API}/simulations/:id`, ({ params }) => {
      const s = studies.find((x) => x.id === params.id);
      return s ? HttpResponse.json(s) : HttpResponse.json({ code: "study_not_found", message: "x" }, { status: 404 });
    }),
    http.get(`${API}/projects/:id/simulations`, () =>
      HttpResponse.json(
        studies.map((s) => ({ id: s.id, alternative_name: s.alternative_name, kind: s.kind, directions_deg: s.directions_deg, status: s.status, progress: 1, device: "auto", created_at: s.created_at })),
      ),
    ),
  ];
}
