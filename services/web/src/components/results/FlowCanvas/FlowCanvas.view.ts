import { useEffect, useRef, useState, type PointerEvent, type WheelEvent } from "react";
import { fitView, screenToCell, zoomAt, type GridView } from "@/engines/fields/grid-view";

interface UseGridView {
  view: GridView;
  onWheel: (e: WheelEvent) => void;
  onPointerDown: (e: PointerEvent) => void;
  onPointerMove: (e: PointerEvent) => boolean;
  onPointerUp: (e: PointerEvent) => [number, number] | null;
  zoomBy: (f: number) => void;
  fit: () => void;
}

function local(e: { clientX: number; clientY: number; currentTarget: Element }): [number, number] {
  const r = e.currentTarget.getBoundingClientRect();
  return [e.clientX - r.left, e.clientY - r.top];
}

/** Fit, wheel zoom around the cursor and drag pan; a click without drag returns its cell. */
export function useGridView(cols: number, rows: number, width: number, height: number): UseGridView {
  const [view, setView] = useState<GridView>(() => fitView(cols, rows, Math.max(width, 1), Math.max(height, 1)));
  const drag = useRef<{ x: number; y: number; moved: boolean } | null>(null);
  const fit = () => setView(fitView(cols, rows, Math.max(width, 1), Math.max(height, 1)));
  useEffect(fit, [cols, rows, width, height]);

  return {
    view,
    fit,
    zoomBy: (f) => setView((v) => zoomAt(v, f, width / 2, height / 2)),
    onWheel: (e) => {
      const [x, y] = local(e);
      setView((v) => zoomAt(v, Math.pow(1.0015, -e.deltaY), x, y));
    },
    onPointerDown: (e) => {
      drag.current = { x: e.clientX, y: e.clientY, moved: false };
      e.currentTarget.setPointerCapture?.(e.pointerId);
    },
    onPointerMove: (e) => {
      const d = drag.current;
      if (!d) return false;
      const dx = e.clientX - d.x;
      const dy = e.clientY - d.y;
      if (!d.moved && Math.hypot(dx, dy) < 4) return false;
      d.moved = true;
      d.x = e.clientX;
      d.y = e.clientY;
      setView((v) => ({ ...v, ox: v.ox + dx, oy: v.oy + dy }));
      return true;
    },
    onPointerUp: (e) => {
      const d = drag.current;
      drag.current = null;
      if (!d || d.moved) return null;
      const [x, y] = local(e);
      return screenToCell(view, rows, x, y);
    },
  };
}
