import { bbox } from "@/engines/geometry/polygon";
import type { Building } from "@/types/geometry/geometry.types";
import type { SceneView } from "@/types/scene/scene-view.types";

export type MeshKind = "building" | "element" | "porous";

export interface MeshSpec {
  id: string;
  kind: MeshKind;
  ring: number[][];
  zMin: number;
  zMax: number;
  opacity: number;
}

const POROUS_OPACITY = 0.35;

/** Draft buildings (live heights) plus the compiled façade solids and porous zones. */
export function toMeshSpecs(buildings: Building[], scene: SceneView | undefined): MeshSpec[] {
  const specs: MeshSpec[] = buildings.map((b) => ({
    id: b.id,
    kind: "building",
    ring: b.footprint,
    zMin: 0,
    zMax: b.height_m ?? 1,
    opacity: 1,
  }));
  for (const s of scene?.solids ?? []) {
    if (s.origin.kind === "building") continue;
    specs.push({ id: s.id, kind: "element", ring: s.footprint, zMin: s.z_min, zMax: s.z_max, opacity: 1 });
  }
  for (const p of scene?.porous ?? []) {
    specs.push({ id: p.id, kind: "porous", ring: p.footprint, zMin: p.z_min, zMax: p.z_max, opacity: POROUS_OPACITY });
  }
  return specs;
}

/** ENU metres → three.js world (y up, north towards −z). */
export function enuToThree([x, y, z]: [number, number, number]): [number, number, number] {
  return [x, z, -y + 0];
}

/** Orbit target at the content centre and a distance that fits it. */
export function frameCamera(specs: MeshSpec[]): { target: [number, number, number]; distance: number } {
  if (!specs.length) return { target: [0, 0, 0], distance: 100 };
  const b = bbox(specs.map((s) => s.ring));
  const top = Math.max(...specs.map((s) => s.zMax));
  const span = Math.max(b.maxX - b.minX, b.maxY - b.minY, top);
  return { target: enuToThree([(b.minX + b.maxX) / 2, (b.minY + b.maxY) / 2, top / 2]), distance: span * 1.8 + 10 };
}

/** Clockwise angle of north from screen-up for an OrbitControls azimuth (radians). */
export function northRotationDeg(azimuthRad: number): number {
  const deg = (azimuthRad * 180) / Math.PI;
  return ((deg % 360) + 360) % 360;
}
