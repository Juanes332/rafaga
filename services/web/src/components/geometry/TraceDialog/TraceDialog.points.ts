import { useState } from "react";
import { measureMetres } from "@/engines/geometry/calibration";
import type { Px } from "@/components/geometry/TraceImage/TraceImage.types";

/** Two-point picker shared by calibration and the ruler. */
export function usePointPair() {
  const [points, setPoints] = useState<Px[]>([]);
  return {
    points,
    pick: (p: Px) => setPoints((prev) => (prev.length >= 2 ? [p] : [...prev, p])),
    clear: () => setPoints([]),
    measure: (mpp: number | null | undefined) => (points.length === 2 && mpp ? measureMetres(points[0], points[1], mpp) : null),
  };
}
