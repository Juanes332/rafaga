import type { TFunction } from "i18next";
import { i18n } from "@/lib/i18n/i18n";
import { formatArea, formatNumber } from "@/lib/format/format.number";

/** BL-12: |mean ΔK| below this many percent is "sin cambio relevante". Mirrored in report_summary.py. */
export const VERDICT_THRESHOLD_PCT = 3;

const CLASSES = ["A", "B", "C", "D", "E"] as const;

export interface ComfortAreas {
  /** m² per Lawson class letter, A (best) to E (worst). */
  classesA: Record<string, number>;
  classesB: Record<string, number>;
  /** Area with gust-safety criteria exceeded (largest of the safety criteria). */
  unsafeA: number;
  unsafeB: number;
}

export interface StrategyInput {
  name: string;
  baseName: string;
  ka: ArrayLike<number>;
  kb: ArrayLike<number>;
  dkReduction: number;
  areas: { reductionM2: number | null; accelA: number; accelB: number };
  comfort?: ComfortAreas;
}

export type Verdict = "improves" | "worsens" | "neutral";

export interface StrategySummary {
  name: string;
  baseName: string;
  verdict: Verdict;
  overallPct: number;
  protectedPct: number | null;
  protectedM2: number;
  accel: { a: number; b: number };
  shift: { from: string; to: string; m2: number } | null;
  improvedM2: number;
  worsenedM2: number;
  unsafe: { a: number; b: number } | null;
}

function pctChange(a: number, b: number, n: number): number | null {
  return n === 0 || a === 0 ? null : (100 * (b - a)) / a;
}

/** Mean K change (percent) overall and over the cells that lose more than |dkReduction|. */
function kChange(ka: ArrayLike<number>, kb: ArrayLike<number>, dk: number) {
  let n = 0, sa = 0, sb = 0, np = 0, pa = 0, pb = 0;
  for (let i = 0; i < ka.length; i += 1) {
    const a = ka[i], b = kb[i];
    if (!Number.isFinite(a) || !Number.isFinite(b)) continue;
    n += 1; sa += a; sb += b;
    if (b - a < dk) { np += 1; pa += a; pb += b; }
  }
  return { overall: pctChange(sa, sb, n) ?? 0, protectedPct: pctChange(pa, pb, np) };
}

function classMoves(c: ComfortAreas) {
  const delta = CLASSES.map((k) => (c.classesB[k] ?? 0) - (c.classesA[k] ?? 0));
  // Cumulative gain of area in "class k or better": a lower bound of the area that crossed each boundary.
  const cumulative = delta.slice(0, -1).map((_, i) => delta.slice(0, i + 1).reduce((s, v) => s + v, 0));
  const improvedM2 = Math.max(0, ...cumulative);
  const worsenedM2 = Math.max(0, ...cumulative.map((v) => -v));
  let from = -1, to = -1;
  delta.forEach((d, i) => {
    if (d < 0 && (from < 0 || d < delta[from])) from = i;
    if (d > 0 && (to < 0 || d > delta[to])) to = i;
  });
  const m2 = from < 0 || to < 0 ? 0 : Math.min(-delta[from], delta[to]);
  return { improvedM2, worsenedM2, shift: m2 >= 1 ? { from: CLASSES[from], to: CLASSES[to], m2 } : null };
}

/** Plain numbers behind the strategy-effect card; no wording here. */
export function summarizeStrategy(i: StrategyInput): StrategySummary {
  const { overall, protectedPct } = kChange(i.ka, i.kb, i.dkReduction);
  const protectedM2 = i.areas.reductionM2 ?? 0;
  const verdict: Verdict = overall <= -VERDICT_THRESHOLD_PCT ? "improves" : overall >= VERDICT_THRESHOLD_PCT ? "worsens" : "neutral";
  const moves = i.comfort ? classMoves(i.comfort) : null;
  return {
    name: i.name,
    baseName: i.baseName,
    verdict,
    overallPct: overall,
    protectedPct: protectedM2 >= 1 ? protectedPct : null,
    protectedM2,
    accel: { a: i.areas.accelA, b: i.areas.accelB },
    shift: moves?.shift ?? null,
    improvedM2: moves?.improvedM2 ?? 0,
    worsenedM2: moves?.worsenedM2 ?? 0,
    unsafe: i.comfort ? { a: i.comfort.unsafeA, b: i.comfort.unsafeB } : null,
  };
}

/** Signed one-decimal percent, e.g. "−5,1 %" (U+2212), for the jargon-allowed details. */
export function signedPct(pct: number): string {
  const sign = pct > 0 ? "+" : pct < 0 ? "−" : "";
  return `${sign}${formatNumber(Math.abs(pct), 1)} %`;
}

/** The summary sentences in the order the card and the PDF show them. */
export function summaryLines(s: StrategySummary, t: TFunction = i18n.t.bind(i18n)): string[] {
  const k = (key: string, o: Record<string, unknown> = {}) => t(`compare:summary.${key}`, o) as string;
  const out: string[] = [];
  const mean = Math.abs(s.overallPct);
  if (s.protectedPct !== null && s.protectedPct < 0) {
    out.push(k("effect.protected", { name: s.name, pct: formatNumber(Math.abs(s.protectedPct), 0), area: formatArea(s.protectedM2) }));
  } else if (s.verdict === "neutral") {
    out.push(k("effect.same", { name: s.name }));
  } else {
    out.push(k(s.verdict === "improves" ? "effect.reducesAvg" : "effect.increasesAvg", { name: s.name, pct: formatNumber(mean, 0) }));
  }
  if (Math.abs(s.accel.b - s.accel.a) >= 1) out.push(k("accel", { a: formatArea(s.accel.a), b: formatArea(s.accel.b) }));
  if (s.shift) {
    out.push(k("shift", { area: formatArea(s.shift.m2), from: s.shift.from, to: s.shift.to, fromName: k(`classes.${s.shift.from}`), toName: k(`classes.${s.shift.to}`) }));
  }
  const imp = s.improvedM2 >= 1, wor = s.worsenedM2 >= 1;
  if (imp && wor) out.push(k("moved.both", { improved: formatArea(s.improvedM2), worsened: formatArea(s.worsenedM2) }));
  else if (imp) out.push(k("moved.improved", { improved: formatArea(s.improvedM2) }));
  else if (wor) out.push(k("moved.worsened", { worsened: formatArea(s.worsenedM2) }));
  if (s.unsafe && (s.unsafe.a >= 1 || s.unsafe.b >= 1) && Math.abs(s.unsafe.b - s.unsafe.a) >= 1) {
    out.push(k("unsafe", { a: formatArea(s.unsafe.a), b: formatArea(s.unsafe.b) }));
  }
  out.push(k(`verdict.${s.verdict}`, { base: s.baseName, threshold: VERDICT_THRESHOLD_PCT }));
  return out;
}
