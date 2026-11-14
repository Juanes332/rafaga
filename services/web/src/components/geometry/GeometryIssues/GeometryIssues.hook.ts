import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { clientIssues } from "@/engines/geometry/buildings";
import { useGeometryStore } from "@/stores/geometry/geometry.store";
import type { GeometryIssue } from "@/types/geometry/geometry.types";

export interface IssueRow {
  key: string;
  buildingId: string | null;
  buildingName: string | null;
  text: string;
}

/** Client checks merged with the last server validation, de-duplicated per building and code. */
export function useGeometryIssues(serverIssues: GeometryIssue[]): { rows: IssueRow[]; onSelect: (id: string) => void } {
  const { t } = useTranslation();
  const buildings = useGeometryStore((s) => s.buildings);
  const rows = useMemo(() => {
    const seen = new Set<string>();
    const names = new Map(buildings.map((b) => [b.id, b.name ?? null]));
    const live = new Set(buildings.map((b) => b.id));
    return [...clientIssues(buildings), ...serverIssues]
      .filter((i) => !i.building_id || live.has(i.building_id))
      .filter((i) => {
        const key = `${i.building_id ?? ""}:${i.code}`;
        return seen.has(key) ? false : (seen.add(key), true);
      })
      .map((i) => ({
        key: `${i.building_id ?? ""}:${i.code}`,
        buildingId: i.building_id ?? null,
        buildingName: i.building_id ? (names.get(i.building_id) ?? null) : null,
        text: t(`geometry:issues.${i.code}`),
      }));
  }, [buildings, serverIssues, t]);
  return { rows, onSelect: (id) => useGeometryStore.getState().select(id) };
}
