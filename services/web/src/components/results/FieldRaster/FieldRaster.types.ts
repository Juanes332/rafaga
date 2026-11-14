import type { Rgb } from "@/engines/colormaps/colormap";
import type { Field } from "@/engines/fields/field.decode";
import type { GridView } from "@/engines/fields/grid-view";

export interface CanvasLayerProps {
  view: GridView;
  width: number;
  height: number;
  className?: string;
}

export interface FieldRasterProps extends CanvasLayerProps {
  field: Field;
  color: (v: number) => Rgb;
  /** 0–255; K draws at 85 % under the particles. */
  alpha?: number;
}
