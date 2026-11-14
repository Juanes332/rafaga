import { useEffect, useRef } from "react";
import { prepareCanvas } from "@/components/results/FieldRaster/FieldRaster.hook";
import type { ZoneKind } from "@/engines/fields/zone-patterns";
import { drawZones } from "./ZoneOverlay.utils";
import type { ZoneOverlayProps } from "./ZoneOverlay.types";

/** Zones as fill + pattern (never colour alone, design-system §2.6). */
export function ZoneOverlay(p: ZoneOverlayProps) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    if (!ref.current || p.width === 0) return;
    const ctx = prepareCanvas(ref.current, p.width, p.height);
    if (!ctx) return;
    const map: Record<ZoneKind, string> = { acceleration: p.colors.accel, stagnation: p.colors.stagnation, reduction: p.colors.reduction };
    drawZones(ctx, p.codes, p.cols, p.rows, p.view, (k) => map[k]);
  }, [p.codes, p.cols, p.rows, p.view, p.width, p.height, p.colors]);
  return <canvas ref={ref} className={p.className} style={{ width: p.width, height: p.height }} aria-hidden />;
}
