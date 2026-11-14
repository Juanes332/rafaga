import { useTranslation } from "react-i18next";
import { formatDate } from "@/lib/format/format.date";
import { formatUnit } from "@/lib/format/format.number";
import type { TerrainCategory } from "@/types/wind/wind.types";
import type { WindPanelProps } from "./WindPanel.types";

interface UseWindPanel {
  sourceNote: string | null;
  densityText: string;
  densityDetail: string | null;
  terrainValue: string;
  onTerrain: (key: string) => void;
}

/** Derived copy for the wind inspector. */
export function useWindPanel(p: WindPanelProps): UseWindPanel {
  const { t } = useTranslation();
  const w = p.wind;
  const date = w?.fetched_at ? formatDate(w.fetched_at) : null;
  const sourceNote = w?.source === "era5" && date ? (w.from_cache ? t("wind:fromCache", { date }) : t("wind:fetchedAt", { date })) : null;
  return {
    sourceNote,
    densityText: formatUnit(p.density, 3, "kg/m³"),
    densityDetail: p.elevation != null ? t("wind:density.detail", { h: formatUnit(p.elevation, 0, "m") }) : null,
    terrainValue: w?.terrain_category ?? "",
    onTerrain: (key) => {
      const cat = p.terrain.find((c: TerrainCategory) => c.key === key);
      if (cat) p.onPatch({ terrain_category: cat.key, z0_m: cat.z0_m });
    },
  };
}
