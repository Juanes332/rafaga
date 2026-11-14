import type { Box, Point } from "@/engines/geometry/polygon";

export interface ViewBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

interface RectLike {
  left: number;
  top: number;
  width: number;
  height: number;
}

const MARGIN = 0.25;

/** SVG viewBox in metres; svg y is −north so the plan reads north-up. */
export function computeViewBox(content: Box | null, zoom: number, pan: [number, number], aspect = 1): ViewBox {
  const fitted = content && Number.isFinite(content.minX);
  const cx = (fitted ? (content.minX + content.maxX) / 2 : 0) + pan[0];
  const cy = (fitted ? (content.minY + content.maxY) / 2 : 0) + pan[1];
  const span = fitted ? Math.max(content.maxX - content.minX, content.maxY - content.minY, 20) * (1 + 2 * MARGIN) : 100;
  const size = span / zoom;
  // Match the canvas aspect so the grid fills it edge to edge.
  const w = aspect >= 1 ? size * aspect : size;
  const h = aspect >= 1 ? size : size / aspect;
  return { x: cx - w / 2, y: -cy - h / 2, w, h };
}

/** Client pixel → world metres for preserveAspectRatio="xMidYMid meet". */
export function clientToWorld(clientX: number, clientY: number, rect: RectLike, vb: ViewBox): Point {
  if (rect.width <= 0 || rect.height <= 0) return [0, 0];
  const scale = Math.min(rect.width / vb.w, rect.height / vb.h);
  const offX = (rect.width - vb.w * scale) / 2;
  const offY = (rect.height - vb.h * scale) / 2;
  const sx = vb.x + (clientX - rect.left - offX) / scale;
  const sy = vb.y + (clientY - rect.top - offY) / scale;
  return [sx, -sy + 0];
}

/** Pixels per metre on screen. */
export function pxPerMetre(rect: RectLike, vb: ViewBox): number {
  return Math.min(rect.width / vb.w, rect.height / vb.h) || 1;
}

export function toSvgPoints(ring: number[][]): string {
  return ring.map(([x, y]) => `${x},${-y + 0}`).join(" ");
}

/** Round bar length (1-2-5 series) no longer than a quarter of the visible span. */
export function niceScaleBar(visibleSpanM: number): number {
  const target = visibleSpanM / 4;
  const pow = 10 ** Math.floor(Math.log10(target));
  for (const m of [5, 2, 1]) if (m * pow <= target) return m * pow;
  return pow;
}

/** Grid lines (svg coords) every `step` metres across the view box. */
export function gridPath(vb: ViewBox, step: number): string {
  const parts: string[] = [];
  const x0 = Math.ceil(vb.x / step) * step;
  for (let x = x0; x <= vb.x + vb.w; x += step) parts.push(`M${x} ${vb.y}V${vb.y + vb.h}`);
  const y0 = Math.ceil(vb.y / step) * step;
  for (let y = y0; y <= vb.y + vb.h; y += step) parts.push(`M${vb.x} ${y}H${vb.x + vb.w}`);
  return parts.join("");
}
