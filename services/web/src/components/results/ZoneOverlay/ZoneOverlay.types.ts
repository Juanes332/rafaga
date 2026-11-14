import type { TokenColors } from "@/hooks/theme/use-token-colors";
import type { CanvasLayerProps } from "@/components/results/FieldRaster/FieldRaster.types";

export interface ZoneOverlayProps extends CanvasLayerProps {
  /** Cell codes from engines/fields/zones (ZONE.*), row 0 = south. */
  codes: Uint8Array;
  cols: number;
  rows: number;
  colors: TokenColors;
}
