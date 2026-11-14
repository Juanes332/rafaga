import { arc } from "d3-shape";
import { scaleSqrt } from "d3-scale";
import { kColor } from "@/engines/colormaps/colormap";
import type { WindSector } from "@/types/wind/wind.types";

export interface PetalArc {
  deg: number;
  outer: number;
  path: string;
  /** Full-length wedge used as the hit area in selection mode. */
  hitPath: string;
  sector: WindSector | null;
}

const HALF = (11.25 * Math.PI) / 180;
const GAP = 0.03;
// Fixed speed domain so colours mean the same on every project.
const SPEED_MAX = 12;

function wedge(deg: number, inner: number, outer: number, gap = GAP): string {
  const a = (deg * Math.PI) / 180;
  return arc()({ innerRadius: inner, outerRadius: outer, startAngle: a - HALF + gap, endAngle: a + HALF - gap }) ?? "";
}

/** 16 petals, area-true radius (sqrt scale) so frequency reads by area, not length. */
export function sectorArcs(sectors: WindSector[] | null, radius: number, inner: number): PetalArc[] {
  const list = sectors ?? [];
  const max = Math.max(0.0001, ...list.map((s) => s.frequency));
  const r = scaleSqrt().domain([0, max]).range([inner, radius]);
  return Array.from({ length: 16 }, (_, i) => {
    const deg = i * 22.5;
    const sector = list.find((s) => Math.abs(s.center_deg - deg) < 1) ?? null;
    const outer = sector ? r(sector.frequency) : inner;
    return { deg, outer, path: wedge(deg, inner, outer), hitPath: wedge(deg, inner, radius, 0.01), sector };
  });
}

/** Fraction of time covered by the chosen directions; null without a rose. */
export function coverage(sectors: WindSector[] | null | undefined, degs: number[]): number | null {
  if (!sectors?.length) return null;
  return sectors.filter((s) => degs.some((d) => Math.abs(d - s.center_deg) < 1)).reduce((a, s) => a + s.frequency, 0);
}

/** Most frequent directions until they cover `target` of the time. */
export function dominantDirections(sectors: WindSector[], target = 0.7): number[] {
  const sorted = [...sectors].sort((a, b) => b.frequency - a.frequency);
  const out: number[] = [];
  let acc = 0;
  for (const s of sorted) {
    if (acc >= target) break;
    out.push(s.center_deg);
    acc += s.frequency;
  }
  return out;
}

export function petalColor(p50: number): string {
  const [r, g, b] = kColor((Math.min(p50, SPEED_MAX) / SPEED_MAX) * 2);
  return `rgb(${r} ${g} ${b})`;
}

export const ROSE_SPEED_MAX = SPEED_MAX;
