import { useCallback, useMemo, useRef, useState, type KeyboardEvent, type PointerEvent } from "react";
import { useTranslation } from "react-i18next";
import { sampleNearest } from "@/engines/fields/field.decode";
import { screenToCell } from "@/engines/fields/grid-view";
import { useReducedMotion } from "@/hooks/media/use-media-query";
import { useElementSize } from "@/hooks/media/use-element-size";
import { useTokenColors } from "@/hooks/theme/use-token-colors";
import type { FlowCanvasProps } from "./FlowCanvas.types";
import { readoutText, scaleBar } from "./FlowCanvas.utils";
import { useGridView } from "./FlowCanvas.view";

interface Readout {
  text: string;
  x: number;
  y: number;
}

/** Plan view logic: size, pan/zoom, hover readout, Space to pause, motion fallback. */
export function useFlowCanvas(p: FlowCanvasProps) {
  const { t } = useTranslation();
  const box = useRef<HTMLDivElement>(null);
  const size = useElementSize(box);
  const g = useGridView(p.K.cols, p.K.rows, size.width, size.height);
  const colors = useTokenColors();
  const reduced = useReducedMotion();
  const [glMissing, setGlMissing] = useState(false);
  const [readout, setReadout] = useState<Readout | null>(null);
  const onUnavailable = useCallback(() => setGlMissing(true), []);
  const staticMode = reduced || glMissing || !p.velocity;
  const lines = useMemo(() => (staticMode ? p.streamlines() : []), [staticMode, p]);

  const hover = (e: PointerEvent) => {
    if (g.onPointerMove(e)) return setReadout(null);
    const r = e.currentTarget.getBoundingClientRect();
    const [x, y] = [e.clientX - r.left, e.clientY - r.top];
    const [cx, cy] = screenToCell(g.view, p.K.rows, x, y);
    const text = readoutText(sampleNearest(p.K, cx, cy), p.speed ? sampleNearest(p.speed, cx, cy) : null, t);
    setReadout(text ? { text, x, y } : null);
  };

  return {
    box,
    size,
    ...g,
    colors,
    lines,
    staticMode,
    staticLabel: reduced ? t("results:flow.static") : t("results:flow.staticNoGl"),
    onUnavailable,
    readout,
    scale: scaleBar(g.view.ppc / p.dxM, g.view.zoom),
    onPointerMove: hover,
    onPointerLeave: () => setReadout(null),
    onPointerUp: (e: PointerEvent) => {
      const cell = g.onPointerUp(e);
      if (cell && p.onCellClick) p.onCellClick(cell[0], cell[1]);
    },
    onKeyDown: (e: KeyboardEvent) => {
      if (e.key !== " ") return;
      e.preventDefault();
      p.onTogglePause();
    },
  };
}
