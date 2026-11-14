export type LegendKind = "k" | "speed" | "dk";

export interface KLegendProps {
  kind: LegendKind;
  /** Upper bound for the speed legend (m/s). */
  max?: number;
  /** Threshold marks (K: accel + stagnation; ΔK: reduction). */
  marks?: number[];
  className?: string;
}

export interface LegendTick {
  value: number;
  label: string;
  /** Position along the bar, 0–100 %. */
  at: number;
}
