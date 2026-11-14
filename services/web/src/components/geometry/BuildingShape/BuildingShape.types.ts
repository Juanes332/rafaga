import type { KeyboardEvent, PointerEvent } from "react";
import type { Building } from "@/types/geometry/geometry.types";

export interface BuildingShapeProps {
  building: Building;
  selected: boolean;
  /** Live drag offset in metres; only the dragged block gets one, so others skip re-render. */
  offset: [number, number] | null;
  interactive: boolean;
  label: string;
  /** Height as shown on the plan, e.g. "36 m". */
  heightText: string;
  /** Text size in metres so labels stay ~12 px at any zoom. */
  fontSize: number;
  onPointerDown: (id: string, e: PointerEvent<SVGGElement>) => void;
  onKeyDown: (id: string, e: KeyboardEvent<SVGGElement>) => void;
}
