import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { backgroundsQueryOptions, useDeleteBackground, useUpdateBackground } from "@/api/geometry/backgrounds.queries";
import { polygonArea } from "@/engines/geometry/polygon";
import { formatNumber, formatUnit } from "@/lib/format/format.number";
import { useGeometryStore } from "@/stores/geometry/geometry.store";

export const SNAP_STEPS = [0, 0.5, 1, 5];

/** Totals, grid snap and the calibrated background's opacity. */
export function useGeometrySummary(projectId: string) {
  const { t } = useTranslation();
  const buildings = useGeometryStore((s) => s.buildings);
  const snapStep = useGeometryStore((s) => s.snapStep);
  const setSnap = useGeometryStore((s) => s.setSnap);
  const backgrounds = useQuery(backgroundsQueryOptions(projectId));
  const update = useUpdateBackground(projectId);
  const remove = useDeleteBackground(projectId);
  const background = backgrounds.data?.filter((b) => b.metres_per_pixel).at(-1) ?? null;
  const total = buildings.reduce((sum, b) => sum + polygonArea(b.footprint), 0);
  return {
    summary: t("geometry:inspector.summary", { count: formatNumber(buildings.length, 0), area: formatUnit(total, 0, "m²") }),
    snapValue: String(snapStep),
    snapOptions: SNAP_STEPS.map((s) => ({
      value: String(s),
      label: s === 0 ? t("geometry:inspector.snapOff") : formatUnit(s, s % 1 ? 1 : 0, "m"),
    })),
    onSnap: (v: string) => setSnap(Number(v)),
    background,
    onOpacity: (opacity: number) => background && update.mutate({ id: background.id, patch: { opacity } }),
    onRemoveBackground: () => background && remove.mutate(background.id),
  };
}
