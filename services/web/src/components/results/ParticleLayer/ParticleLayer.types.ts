import type { VelocityData } from "@/engines/particles/particles.math";
import type { CanvasLayerProps } from "@/components/results/FieldRaster/FieldRaster.types";

export interface ParticleLayerProps extends CanvasLayerProps {
  data: VelocityData;
  cols: number;
  rows: number;
  paused: boolean;
  /** CSS colour of the particles (ink token). */
  ink: string;
  /** Called once when WebGL2 is unavailable → the view switches to static streamlines. */
  onUnavailable: () => void;
}
