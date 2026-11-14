import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { directionLabel } from "@/lib/format/format.direction";
import { formatPercent, formatUnit } from "@/lib/format/format.number";
import type { WindRoseProps } from "./WindRose.types";
import { petalColor, sectorArcs, type PetalArc } from "./WindRose.utils";

export interface Petal extends PetalArc {
  label: string;
  fill: string;
  selected: boolean;
}

interface UseWindRose {
  half: number;
  radius: number;
  inner: number;
  rings: number[];
  petals: Petal[];
  selectable: boolean;
  onKey: (deg: number, key: string) => void;
}

/** Geometry and accessible labels for the 16-sector rose. */
export function useWindRose({ sectors, size = 360, selected, onToggle }: WindRoseProps): UseWindRose {
  const { t } = useTranslation();
  const half = size / 2;
  // Room for two-line axis labels (name over degrees) outside the petals.
  const radius = half - 38;
  const inner = Math.max(8, radius * 0.08);
  const petals = useMemo(
    () =>
      sectorArcs(sectors, radius, inner).map((a) => ({
        ...a,
        fill: a.sector ? petalColor(a.sector.p50_ms) : "transparent",
        selected: selected?.some((d) => Math.abs(d - a.deg) < 1) ?? false,
        label: a.sector
          ? t("wind:rose.sector", { dir: directionLabel(a.deg), freq: formatPercent(a.sector.frequency), p50: formatUnit(a.sector.p50_ms, 1, "m/s") })
          : directionLabel(a.deg),
      })),
    [sectors, radius, inner, selected, t],
  );
  return {
    half,
    radius,
    inner,
    rings: [0.25, 0.5, 0.75, 1].map((f) => inner + (radius - inner) * f),
    petals,
    selectable: Boolean(onToggle),
    onKey: (deg, key) => {
      if (key === " " || key === "Enter") onToggle?.(deg);
    },
  };
}
