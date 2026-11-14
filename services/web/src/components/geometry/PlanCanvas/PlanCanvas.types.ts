import type { Point } from "@/engines/geometry/polygon";

export interface PlanCanvasProps {
  projectId: string;
  readOnly: boolean;
}

export type Gesture =
  | { kind: "none" }
  | { kind: "rect"; a: Point; b: Point }
  | { kind: "move"; id: string; start: Point; delta: [number, number] }
  | { kind: "pan"; last: [number, number] };

/** Converts a pointer event to world metres, optionally snapped to the grid. */
export type ToWorld = (e: { clientX: number; clientY: number }, snapped?: boolean) => Point;
