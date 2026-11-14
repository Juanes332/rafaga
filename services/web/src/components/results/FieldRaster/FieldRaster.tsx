import { useFieldRaster } from "./FieldRaster.hook";
import type { FieldRasterProps } from "./FieldRaster.types";

/** A result field painted with a fixed-domain cmocean LUT. */
export function FieldRaster(props: FieldRasterProps) {
  const ref = useFieldRaster(props);
  return <canvas ref={ref} className={props.className} style={{ width: props.width, height: props.height }} aria-hidden />;
}
