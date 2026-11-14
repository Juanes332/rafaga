import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { addBuilding, moveBuilding } from "@/engines/geometry/buildings";
import { polygonArea, rectFromCorners, type Point, type Ring } from "@/engines/geometry/polygon";
import { useGeometryStore } from "@/stores/geometry/geometry.store";

const MIN_AREA_M2 = 1;

/** Commits drawn shapes and moves to the undo stack, then selects the result. */
export function useCommitShape() {
  const { t } = useTranslation();
  return useCallback(
    (ring: Ring) => {
      const s = useGeometryStore.getState();
      if (polygonArea(ring) < MIN_AREA_M2) return false;
      const next = addBuilding(s.buildings, ring, t("geometry:blockName", { n: s.buildings.length + 1 }));
      s.apply(next);
      s.setTool("select");
      s.select(next[next.length - 1].id);
      return true;
    },
    [t],
  );
}

export function commitMove(id: string, delta: [number, number]): void {
  if (delta[0] === 0 && delta[1] === 0) return;
  const s = useGeometryStore.getState();
  s.apply(moveBuilding(s.buildings, id, delta[0], delta[1]));
}

export function commitRect(a: Point, b: Point, commit: (r: Ring) => boolean): boolean {
  return commit(rectFromCorners(a, b));
}

interface PolygonTool {
  points: Point[];
  hover: Point | null;
  add: (p: Point, closeRadius: number) => void;
  setHover: (p: Point | null) => void;
  finish: () => void;
  cancel: () => void;
}

/** Click-by-click polygon; closes on the first vertex, double click or Enter. */
export function usePolygonTool(commit: (r: Ring) => boolean): PolygonTool {
  const [points, setPoints] = useState<Point[]>([]);
  const [hover, setHover] = useState<Point | null>(null);
  const finish = () => {
    if (points.length >= 3) commit(points);
    setPoints([]);
  };
  const add = (p: Point, closeRadius: number) => {
    const first = points[0];
    if (first && points.length >= 3 && Math.hypot(p[0] - first[0], p[1] - first[1]) <= closeRadius) return finish();
    const last = points.at(-1);
    if (last && last[0] === p[0] && last[1] === p[1]) return;
    setPoints([...points, p]);
  };
  return { points, hover, add, setHover, finish, cancel: () => setPoints([]) };
}

/** Two-click ruler; a third click starts a new measurement. */
export function useRulerTool() {
  const [points, setPoints] = useState<Point[]>([]);
  const add = (p: Point) => setPoints((prev) => (prev.length >= 2 ? [p] : [...prev, p]));
  const distance = points.length === 2 ? Math.hypot(points[1][0] - points[0][0], points[1][1] - points[0][1]) : null;
  return { points, distance, add, clear: () => setPoints([]) };
}
