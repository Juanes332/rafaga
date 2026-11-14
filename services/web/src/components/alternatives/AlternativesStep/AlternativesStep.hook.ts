import { useQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { useShallow } from "zustand/react/shallow";
import { alternativesQueryOptions } from "@/api/alternatives/alternatives.queries";
import { facadeElementsQueryOptions } from "@/api/facades/facades.queries";
import { geometryQueryOptions } from "@/api/geometry/geometry.queries";
import { useProjectAccess } from "@/hooks/access/use-project-access";
import { useFacadesStore, type EdgeRef } from "@/stores/facades/facades.store";
import type { Alternative } from "@/types/alternatives/alternative.types";
import type { FacadeElement } from "@/types/facades/facade.types";
import type { Building } from "@/types/geometry/geometry.types";

export interface UseAlternativesStep {
  projectId: string;
  loading: boolean;
  alternatives: Alternative[];
  current: Alternative | null;
  buildings: Building[];
  elements: FacadeElement[];
  edge: EdgeRef | null;
  edgeElement: FacadeElement | null;
  readOnly: boolean;
  onlyBase: boolean;
  buildingName: (id: string) => string;
  selectAlternative: (id: string) => void;
  selectEdge: (edge: EdgeRef) => void;
}

/** Picks the open alternative (stored choice, else the first non-base one) and its elements. */
export function useAlternativesStep(): UseAlternativesStep {
  const { projectId } = useParams({ strict: false }) as { projectId: string };
  const alternatives = useQuery(alternativesQueryOptions(projectId));
  const geometry = useQuery(geometryQueryOptions(projectId));
  const { readOnly } = useProjectAccess(projectId);
  const { alternativeId, edge, selectAlternative, selectEdge } = useFacadesStore(
    useShallow((st) => ({ alternativeId: st.alternativeId, edge: st.edge, selectAlternative: st.selectAlternative, selectEdge: st.selectEdge })),
  );
  const list = alternatives.data ?? [];
  const current = list.find((a) => a.id === alternativeId) ?? list.find((a) => !a.is_base) ?? list[0] ?? null;
  const elements = useQuery({ ...facadeElementsQueryOptions(current?.id ?? ""), enabled: Boolean(current && !current.is_base) });
  const buildings = geometry.data?.buildings ?? [];
  const els = current?.is_base ? [] : (elements.data ?? []);
  return {
    projectId,
    loading: alternatives.isLoading || geometry.isLoading,
    alternatives: list,
    current,
    buildings,
    elements: els,
    edge: current?.is_base ? null : edge,
    edgeElement: edge ? (els.find((e) => e.building_id === edge.buildingId && e.edge_index === edge.edgeIndex) ?? null) : null,
    readOnly,
    onlyBase: list.length > 0 && list.every((a) => a.is_base),
    buildingName: (id) => {
      const i = buildings.findIndex((b) => b.id === id);
      return buildings[i]?.name ?? `${i + 1}`;
    },
    selectAlternative,
    selectEdge,
  };
}
