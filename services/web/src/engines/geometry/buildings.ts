import type { Building, GeometryIssue } from "@/types/geometry/geometry.types";
import { centroid, ensureCcw, scaleAbout, selfIntersects, translate, type Ring } from "./polygon";

/** Default height of a drawn block (SCR-06). */
export const DEFAULT_HEIGHT_M = 12;
export const HEIGHT_RANGE: readonly [number, number] = [1, 500];

function newId(): string {
  return globalThis.crypto.randomUUID();
}

export function addBuilding(list: Building[], footprint: Ring, name: string, source: Building["source"] = "draw"): Building[] {
  const building: Building = {
    id: newId(),
    name,
    footprint: ensureCcw(footprint),
    holes: [],
    height_m: DEFAULT_HEIGHT_M,
    source,
    missing_height: false,
  };
  return [...list, building];
}

export function updateBuilding(list: Building[], id: string, patch: Partial<Building>): Building[] {
  return list.map((b) => {
    if (b.id !== id) return b;
    const next = { ...b, ...patch };
    if (patch.height_m != null) next.missing_height = false;
    return next;
  });
}

export function moveBuilding(list: Building[], id: string, dx: number, dy: number): Building[] {
  return list.map((b) => (b.id === id ? { ...b, footprint: translate(b.footprint, dx, dy), holes: (b.holes ?? []).map((h) => translate(h, dx, dy)) } : b));
}

/** Uniform scale about the footprint's bounding-box centre. */
export function scaleBuilding(list: Building[], id: string, factor: number): Building[] {
  return list.map((b) => {
    if (b.id !== id) return b;
    const c = centroid(b.footprint);
    return { ...b, footprint: scaleAbout(b.footprint, c, factor), holes: (b.holes ?? []).map((h) => scaleAbout(h, c, factor)) };
  });
}

export function removeBuilding(list: Building[], id: string): Building[] {
  return list.filter((b) => b.id !== id);
}

/** Issues the editor can see before asking the server (BR-14 subset). */
export function clientIssues(list: Building[]): GeometryIssue[] {
  const issues: GeometryIssue[] = [];
  for (const b of list) {
    const push = (code: GeometryIssue["code"]) => issues.push({ building_id: b.id, code, message_key: `geometry.${code}`, location: null });
    if (selfIntersects(b.footprint)) push("self_intersection");
    if (b.height_m == null) push("missing_height");
    else if (b.height_m < HEIGHT_RANGE[0] || b.height_m > HEIGHT_RANGE[1]) push("height_out_of_range");
  }
  return issues;
}
