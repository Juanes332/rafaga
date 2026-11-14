/** Planar polygon helpers in local ENU metres. Rings are open (closing vertex not repeated). */
export type Point = [number, number];
export type Ring = number[][];

export interface Box {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

/** Shoelace area; positive for counter-clockwise rings. */
export function signedArea(ring: Ring): number {
  let s = 0;
  for (let i = 0; i < ring.length; i += 1) {
    const [x1, y1] = ring[i];
    const [x2, y2] = ring[(i + 1) % ring.length];
    s += x1 * y2 - x2 * y1;
  }
  return s / 2;
}

export function polygonArea(ring: Ring): number {
  return Math.abs(signedArea(ring));
}

/** The contract stores outer rings CCW. */
export function ensureCcw(ring: Ring): Ring {
  return signedArea(ring) < 0 ? [...ring].reverse() : ring;
}

function cross(o: number[], a: number[], b: number[]): number {
  return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
}

function segmentsCross(p1: number[], p2: number[], p3: number[], p4: number[]): boolean {
  const d1 = cross(p3, p4, p1);
  const d2 = cross(p3, p4, p2);
  const d3 = cross(p1, p2, p3);
  const d4 = cross(p1, p2, p4);
  return ((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0)) && ((d3 > 0 && d4 < 0) || (d3 < 0 && d4 > 0));
}

/** True when two non-adjacent edges properly cross (O(n²), fine for building footprints). */
export function selfIntersects(ring: Ring): boolean {
  const n = ring.length;
  for (let i = 0; i < n; i += 1) {
    for (let j = i + 2; j < n; j += 1) {
      if (i === 0 && j === n - 1) continue;
      if (segmentsCross(ring[i], ring[(i + 1) % n], ring[j], ring[(j + 1) % n])) return true;
    }
  }
  return false;
}

/** Even-odd ray casting. */
export function pointInPolygon([x, y]: Point, ring: Ring): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i, i += 1) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

/** Round to the grid step; step 0 disables snapping. */
export function snap([x, y]: Point, step: number): Point {
  if (step <= 0) return [x, y];
  const r = (v: number) => Math.round(v / step) * step + 0;
  return [r(x), r(y)];
}

export function rectFromCorners(a: Point, b: Point): Ring {
  const [x0, x1] = [Math.min(a[0], b[0]), Math.max(a[0], b[0])];
  const [y0, y1] = [Math.min(a[1], b[1]), Math.max(a[1], b[1])];
  return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]];
}

export function translate(ring: Ring, dx: number, dy: number): Ring {
  return ring.map(([x, y]) => [x + dx, y + dy]);
}

export function scaleAbout(ring: Ring, [cx, cy]: Point, factor: number): Ring {
  return ring.map(([x, y]) => [cx + (x - cx) * factor, cy + (y - cy) * factor]);
}

export function bbox(rings: Ring[]): Box {
  const box = { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity };
  for (const ring of rings) {
    for (const [x, y] of ring) {
      box.minX = Math.min(box.minX, x);
      box.minY = Math.min(box.minY, y);
      box.maxX = Math.max(box.maxX, x);
      box.maxY = Math.max(box.maxY, y);
    }
  }
  return box;
}

export function centroid(ring: Ring): Point {
  const b = bbox([ring]);
  return [(b.minX + b.maxX) / 2, (b.minY + b.maxY) / 2];
}

function distanceToSegment([px, py]: Point, a: number[], b: number[]): number {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const len2 = dx * dx + dy * dy || 1;
  const t = Math.max(0, Math.min(1, ((px - a[0]) * dx + (py - a[1]) * dy) / len2));
  return Math.hypot(px - (a[0] + t * dx), py - (a[1] + t * dy));
}

/** Closest edge (index i = vertex i → i+1) to a point; used for façade selection. */
export function nearestEdge(p: Point, ring: Ring): { index: number; distance: number } {
  let best = { index: 0, distance: Infinity };
  for (let i = 0; i < ring.length; i += 1) {
    const d = distanceToSegment(p, ring[i], ring[(i + 1) % ring.length]);
    if (d < best.distance) best = { index: i, distance: d };
  }
  return best;
}
