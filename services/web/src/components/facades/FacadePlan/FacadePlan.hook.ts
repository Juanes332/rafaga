import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { formatUnit } from "@/lib/format/format.number";
import type { StrategyType } from "@/types/facades/facade.types";
import type { FacadePlanProps } from "./FacadePlan.types";
import { buildingEdges, offsetSegment, planViewBox, ringPoints, type PlanEdge, type ViewBox } from "./FacadePlan.utils";

export interface PlanEdgeView extends PlanEdge {
  key: string;
  buildingId: string;
  label: string;
  selected: boolean;
  strategy: StrategyType | null;
  strategySegment: [number, number, number, number] | null;
}

interface PlanBuildingView {
  id: string;
  name: string;
  centre: [number, number];
  points: string;
  edges: PlanEdgeView[];
}

/** Metric plan geometry plus accessible names for every façade edge. */
export function useFacadePlan(p: FacadePlanProps): { viewBox: ViewBox; buildings: PlanBuildingView[] } {
  const { t } = useTranslation();
  return useMemo(() => {
    const viewBox = planViewBox(p.buildings, 12);
    const buildings = p.buildings.map((b, bi) => {
      const name = b.name ?? `${bi + 1}`;
      const edges = buildingEdges(b).map((e) => {
        const el = p.elements.find((x) => x.building_id === b.id && x.edge_index === e.index && !x.orphaned);
        return {
          ...e,
          key: `${b.id}-${e.index}`,
          buildingId: b.id,
          label: t("alternatives:plan.edge", { index: e.index + 1, building: name, length: formatUnit(e.length, 1, "m") }),
          selected: p.selected?.buildingId === b.id && p.selected.edgeIndex === e.index,
          strategy: el?.type ?? null,
          strategySegment: el ? offsetSegment(e, 1.6) : null,
        };
      });
      const ring = b.footprint as [number, number][];
      const centre: [number, number] = [ring.reduce((a, q) => a + q[0], 0) / ring.length, -ring.reduce((a, q) => a + q[1], 0) / ring.length];
      return { id: b.id, name, centre, points: ringPoints(b), edges };
    });
    return { viewBox, buildings };
  }, [p.buildings, p.elements, p.selected, t]);
}
