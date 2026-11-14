import { useTranslation } from "react-i18next";
import { removeBuilding, scaleBuilding, updateBuilding } from "@/engines/geometry/buildings";
import { polygonArea } from "@/engines/geometry/polygon";
import { formatUnit } from "@/lib/format/format.number";
import { useGeometryStore } from "@/stores/geometry/geometry.store";
import type { Building } from "@/types/geometry/geometry.types";

interface UseBuildingInspector {
  building: Building | null;
  areaText: string;
  sourceText: string;
  onName: (name: string) => void;
  onHeight: (h: number) => void;
  onGrow: () => void;
  onShrink: () => void;
  onDelete: () => void;
}

/** Edits of the selected building, each one an undoable step. */
export function useBuildingInspector(): UseBuildingInspector {
  const { t } = useTranslation();
  const building = useGeometryStore((s) => s.buildings.find((b) => b.id === s.selectedId) ?? null);
  const edit = (fn: (list: Building[], id: string) => Building[]) => {
    const s = useGeometryStore.getState();
    if (s.selectedId) s.apply(fn(s.buildings, s.selectedId));
  };
  return {
    building,
    areaText: building ? formatUnit(polygonArea(building.footprint), 0, "m²") : "",
    sourceText: building ? t(`geometry:sources.${building.source}`) : "",
    onName: (name) => name.trim() && name !== building?.name && edit((l, id) => updateBuilding(l, id, { name: name.trim() })),
    onHeight: (h) => edit((l, id) => updateBuilding(l, id, { height_m: h })),
    onGrow: () => edit((l, id) => scaleBuilding(l, id, 1.1)),
    onShrink: () => edit((l, id) => scaleBuilding(l, id, 1 / 1.1)),
    onDelete: () => {
      edit(removeBuilding);
      useGeometryStore.getState().select(null);
    },
  };
}
