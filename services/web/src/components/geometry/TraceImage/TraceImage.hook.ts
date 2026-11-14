import { useState, type MouseEvent, type SyntheticEvent } from "react";
import type { Px, TraceImageProps } from "./TraceImage.types";

/** Converts clicks on the scaled image back to natural pixels, the unit calibration uses. */
export function useTraceImage({ onPick }: Pick<TraceImageProps, "onPick">) {
  const [natural, setNatural] = useState<Px>([1, 1]);
  const onLoad = (e: SyntheticEvent<HTMLImageElement>) =>
    setNatural([e.currentTarget.naturalWidth || 1, e.currentTarget.naturalHeight || 1]);
  const onClick = (e: MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return;
    onPick([((e.clientX - rect.left) / rect.width) * natural[0], ((e.clientY - rect.top) / rect.height) * natural[1]]);
  };
  return { natural, onLoad, onClick };
}
