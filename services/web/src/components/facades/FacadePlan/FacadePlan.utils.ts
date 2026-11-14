import type { Building } from "@/types/geometry/geometry.types";

export interface PlanEdge {
  index: number;
  a: [number, number];
  b: [number, number];
  length: number;
  /** Unit outward normal (footprints are CCW). */
  normal: [number, number];
}

/** Edges of a footprint ring (closing vertex not repeated). */
export function buildingEdges(b: Building): PlanEdge[] {
  const ring = b.footprint as [number, number][];
  return ring.map((a, i) => {
    const next = ring[(i + 1) % ring.length];
    const dx = next[0] - a[0];
    const dy = next[1] - a[1];
    const length = Math.hypot(dx, dy) || 1;
    return { index: i, a, b: next, length, normal: [dy / length, -dx / length] };
  });
}

export interface ViewBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

/** SVG viewBox in metres; SVG y grows down, so north-up plans use −y. */
export function planViewBox(buildings: Building[], margin: number): ViewBox {
  const pts = buildings.flatMap((b) => b.footprint as [number, number][]);
  if (pts.length === 0) return { x: -50, y: -50, width: 100, height: 100 };
  const xs = pts.map((p) => p[0]);
  const ys = pts.map((p) => -p[1]);
  const x = Math.min(...xs) - margin;
  const y = Math.min(...ys) - margin;
  return { x, y, width: Math.max(...xs) + margin - x, height: Math.max(...ys) + margin - y };
}

/** Polygon points attribute with y flipped. */
export function ringPoints(b: Building): string {
  return (b.footprint as [number, number][]).map(([x, y]) => `${x},${-y}`).join(" ");
}

/** A segment parallel to the edge, `d` metres outside it (where the strategy sits). */
export function offsetSegment(e: PlanEdge, d: number): [number, number, number, number] {
  const [nx, ny] = e.normal;
  return [e.a[0] + nx * d, -(e.a[1] + ny * d), e.b[0] + nx * d, -(e.b[1] + ny * d)];
}
