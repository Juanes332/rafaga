import { useEffect, useMemo, useRef, type RefObject } from "react";
import { rasterize } from "@/engines/fields/field.raster";
import type { FieldRasterProps } from "./FieldRaster.types";

/** Prepare a sharp-sized canvas: CSS size × devicePixelRatio, scaled context. */
export function prepareCanvas(canvas: HTMLCanvasElement, width: number, height: number): CanvasRenderingContext2D | null {
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.round(width * dpr));
  canvas.height = Math.max(1, Math.round(height * dpr));
  const ctx = canvas.getContext?.("2d") ?? null;
  ctx?.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx?.clearRect(0, 0, width, height);
  return ctx;
}

/** Grid-sized image of the field, then scaled to the view with smoothing (bilinear look). */
export function useFieldRaster(p: FieldRasterProps): RefObject<HTMLCanvasElement | null> {
  const ref = useRef<HTMLCanvasElement>(null);
  const image = useMemo(() => {
    if (typeof document === "undefined") return null;
    const c = document.createElement("canvas");
    c.width = p.field.cols;
    c.height = p.field.rows;
    const ctx = c.getContext?.("2d");
    if (!ctx) return null;
    ctx.putImageData(new ImageData(rasterize(p.field, p.color, p.alpha ?? 255) as Uint8ClampedArray<ArrayBuffer>, p.field.cols, p.field.rows), 0, 0);
    return c;
  }, [p.field, p.color, p.alpha]);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !image || p.width === 0) return;
    const ctx = prepareCanvas(canvas, p.width, p.height);
    if (!ctx) return;
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(image, p.view.ox, p.view.oy, p.field.cols * p.view.ppc, p.field.rows * p.view.ppc);
  }, [image, p.view, p.width, p.height, p.field]);
  return ref;
}
