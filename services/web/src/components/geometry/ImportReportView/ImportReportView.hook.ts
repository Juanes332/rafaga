import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useGeometryStore } from "@/stores/geometry/geometry.store";
import type { ImportReport } from "@/types/geometry/geometry.types";

/** Heights typed for buildings the file left without one. */
export function useImportReportView(report: ImportReport) {
  const { t } = useTranslation();
  const buildings = useGeometryStore((s) => s.buildings);
  const [heights, setHeights] = useState<Record<string, number>>({});
  const missing = report.missing_height.map((id) => ({ id, name: buildings.find((b) => b.id === id)?.name ?? id }));
  return {
    missing,
    heights,
    setHeight: (id: string, h: number) => setHeights((prev) => ({ ...prev, [id]: h })),
    allSet: missing.every((m) => heights[m.id] != null),
    unitText:
      report.detected_unit === "unknown" ? t("geometry:import.unknownUnit") : t(`geometry:import.units.${report.detected_unit}`).toLowerCase(),
    reasonText: (reason: string) => {
      const key = `geometry:import.reasons.${reason}`;
      return t(key) === key ? reason : t(key);
    },
  };
}
