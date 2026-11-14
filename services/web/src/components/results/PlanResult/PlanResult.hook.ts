import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useShallow } from "zustand/react/shallow";
import { geometryQueryOptions } from "@/api/geometry/geometry.queries";
import { settingsQueryOptions } from "@/api/settings/settings.queries";
import { cellToEnu } from "@/engines/fields/grid-view";
import { ZONE, classifyZones, largestBlob } from "@/engines/fields/zones";
import type { ZoneLabel } from "@/components/results/PlanOverlay/PlanOverlay.types";
import { useResultsStore } from "@/stores/results/results.store";
import type { OutputGridPlan } from "@/types/simulations/simulation.types";
import { usePlanData } from "./PlanResult.data";
import type { PlanResultProps } from "./PlanResult.types";

const DEFAULT_T = { k_accel: 1.2, k_stagnation: 0.3, dk_reduction: -0.1 };

/** Plan view orchestration: data, zones re-thresholded client-side, section clicks. */
export function usePlanResult({ projectId, result }: PlanResultProps) {
  const ui = useResultsStore(
    useShallow((s) => ({ layer: s.layer, zones: s.zones, paused: s.paused, tool: s.tool, section: s.section, togglePaused: s.togglePaused, addPoint: s.addSectionPoint })),
  );
  const grid = result.output_grid as OutputGridPlan;
  const data = usePlanData(result.id, ui.layer);
  const settings = useQuery(settingsQueryOptions());
  const geometry = useQuery(geometryQueryOptions(projectId));
  const thresholds = settings.data?.thresholds ?? DEFAULT_T;
  const codes = useMemo(
    () => (ui.zones && data.K ? classifyZones(data.K, thresholds) : null),
    [ui.zones, data.K, thresholds],
  );
  const labels = useMemo((): ZoneLabel[] => {
    if (!codes || !data.K) return [];
    const kinds = [["acceleration", ZONE.acceleration], ["stagnation", ZONE.stagnation]] as const;
    return kinds.flatMap(([zone, code]) => {
      const blob = largestBlob(codes, data.K!.cols, data.K!.rows, code);
      return blob ? [{ zone, blob }] : [];
    });
  }, [codes, data.K]);
  return {
    ...ui,
    grid,
    data,
    thresholds,
    codes,
    labels,
    buildings: geometry.data?.buildings ?? [],
    onCellClick: ui.tool === "section" ? (cx: number, cy: number) => ui.addPoint(cellToEnu(grid, cx, cy)) : undefined,
  };
}
