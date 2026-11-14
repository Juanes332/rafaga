import type { ReactNode } from "react";
import type { Rgb } from "@/engines/colormaps/colormap";
import type { Field } from "@/engines/fields/field.decode";
import type { GridView } from "@/engines/fields/grid-view";
import type { VelocityData } from "@/engines/particles/particles.math";

export interface FlowCanvasProps {
  /** Field painted underneath (K, speed or Lawson class). */
  paint: Field;
  paintColor: (v: number) => Rgb;
  K: Field;
  speed: Field | null;
  velocity: VelocityData | null;
  /** Streamlines for the static fallback, computed lazily by the caller. */
  streamlines: () => number[][];
  zoneCodes: Uint8Array | null;
  paused: boolean;
  onTogglePause: () => void;
  /** Click on the plan in cell units (section tool). */
  onCellClick?: (cx: number, cy: number) => void;
  /** SVG overlay drawn in screen px: buildings, labels, section line. */
  overlay?: (view: GridView) => ReactNode;
  legend?: ReactNode;
  /** Metres per cell, for the scale bar. */
  dxM: number;
}
