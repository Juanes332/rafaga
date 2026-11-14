import { useCallback, type KeyboardEvent } from "react";
import { moveBuilding, removeBuilding, scaleBuilding } from "@/engines/geometry/buildings";
import { useGeometryStore } from "@/stores/geometry/geometry.store";

const ARROWS: Record<string, [number, number]> = {
  ArrowLeft: [-1, 0],
  ArrowRight: [1, 0],
  ArrowUp: [0, 1],
  ArrowDown: [0, -1],
};

/** Keyboard editing of a focused block: arrows nudge, Shift ×10, +/− scale, Delete removes. */
export function useShapeKeys(interactive: boolean) {
  return useCallback(
    (id: string, e: KeyboardEvent<SVGGElement>) => {
      const s = useGeometryStore.getState();
      if (e.key === "Enter" || e.key === " ") return void (e.preventDefault(), s.select(id));
      if (!interactive) return;
      const dir = ARROWS[e.key];
      const step = (s.snapStep || 0.5) * (e.shiftKey ? 10 : 1);
      if (dir) s.apply(moveBuilding(s.buildings, id, dir[0] * step, dir[1] * step));
      else if (e.key === "Delete" || e.key === "Backspace") {
        s.apply(removeBuilding(s.buildings, id));
        s.select(null);
      } else if (e.key === "+" || e.key === "=") s.apply(scaleBuilding(s.buildings, id, 1.1));
      else if (e.key === "-") s.apply(scaleBuilding(s.buildings, id, 1 / 1.1));
      else return;
      e.preventDefault();
      s.select(id);
    },
    [interactive],
  );
}
