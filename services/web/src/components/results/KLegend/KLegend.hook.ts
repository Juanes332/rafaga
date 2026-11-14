import { useTranslation } from "react-i18next";
import { BALANCE_LUT, DK_DOMAIN, DK_TICKS, K_DOMAIN, K_TICKS, SPEED_LUT, lutGradient } from "@/engines/colormaps/colormap";
import { formatNumber } from "@/lib/format/format.number";
import type { KLegendProps, LegendTick } from "./KLegend.types";

interface UseKLegend {
  title: string;
  gradient: string;
  ticks: LegendTick[];
  marks: LegendTick[];
  saturationLabel: string;
  bothEnds: boolean;
}

function domainFor(p: KLegendProps): readonly [number, number] {
  if (p.kind === "dk") return DK_DOMAIN;
  if (p.kind === "speed") return [0, Math.max(1, Math.ceil(p.max ?? 10))];
  return K_DOMAIN;
}

function ticksFor(p: KLegendProps, [, hi]: readonly [number, number]): number[] {
  if (p.kind === "k") return K_TICKS;
  if (p.kind === "dk") return DK_TICKS;
  const step = hi <= 6 ? 1 : hi <= 12 ? 2 : 5;
  return Array.from({ length: Math.floor(hi / step) + 1 }, (_, i) => i * step);
}

/** Fixed-domain numeric legend: ticks, threshold marks and saturation note. */
export function useKLegend(p: KLegendProps): UseKLegend {
  const { t } = useTranslation();
  const domain = domainFor(p);
  const [lo, hi] = domain;
  const at = (v: number) => ((v - lo) / (hi - lo)) * 100;
  const decimals = p.kind === "speed" ? 0 : 1;
  const label = (v: number) => (p.kind === "dk" && v > 0 ? "+" : "") + formatNumber(v, decimals);
  return {
    title: t(`results:legend.${p.kind}`),
    gradient: lutGradient(p.kind === "dk" ? BALANCE_LUT : SPEED_LUT),
    ticks: ticksFor(p, domain).map((v) => ({ value: v, label: label(v), at: at(v) })),
    marks: (p.marks ?? []).filter((m) => m > lo && m < hi).map((v) => ({ value: v, label: formatNumber(v, 2), at: at(v) })),
    saturationLabel: t("results:legend.saturated", { max: label(hi) }),
    bothEnds: p.kind === "dk",
  };
}
