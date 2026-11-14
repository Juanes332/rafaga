import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { formatNumber } from "@/lib/format/format.number";
import { signedPct, summarizeStrategy, summaryLines, VERDICT_THRESHOLD_PCT, type ComfortAreas } from "@/lib/compare/strategy-summary";
import type { Comfort } from "@/types/results/result.types";
import type { StrategySummaryProps } from "./StrategySummary.types";

function classes(c: Comfort): Record<string, number> {
  return Object.fromEntries((c.class_areas ?? []).map((r) => [String(r.class), r.area_m2]));
}

function toComfortAreas(a: Comfort | undefined, b: Comfort | undefined): ComfortAreas | undefined {
  if (!a?.class_areas?.length || !b?.class_areas?.length) return undefined;
  const unsafe = (c: Comfort) => Math.max(0, ...(c.safety_areas ?? []).map((s) => s.area_m2 ?? 0));
  return { classesA: classes(a), classesB: classes(b), unsafeA: unsafe(a), unsafeB: unsafe(b) };
}

/** Numbers, sentences and jargon-allowed details of the strategy-effect card. */
export function useStrategySummary(p: StrategySummaryProps) {
  const { t } = useTranslation();
  return useMemo(() => {
    const acc = (side: "a" | "b") => p.areas?.[side].zones.find((z) => z.zone === "acceleration")?.area_m2 ?? 0;
    const summary = summarizeStrategy({
      name: p.nameB,
      baseName: p.nameA,
      ka: p.ka.data,
      kb: p.kb.data,
      dkReduction: p.dkReduction,
      areas: { reductionM2: p.areas?.reduction.area_m2 ?? null, accelA: acc("a"), accelB: acc("b") },
      comfort: toComfortAreas(p.comfort?.a, p.comfort?.b),
    });
    const details = [t("compare:summary.detailsMean", { pct: signedPct(summary.overallPct), threshold: VERDICT_THRESHOLD_PCT })];
    if (summary.protectedPct !== null) {
      details.push(t("compare:summary.detailsProtected", { dk: formatNumber(Math.abs(p.dkReduction), 2), pct: signedPct(summary.protectedPct) }));
    }
    return { summary, lines: summaryLines(summary, t), details };
  }, [p.areas, p.comfort, p.dkReduction, p.ka, p.kb, p.nameA, p.nameB, t]);
}
