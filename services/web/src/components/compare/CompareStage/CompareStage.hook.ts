import { useMemo, useRef, useState, type PointerEvent } from "react";
import { useShallow } from "zustand/react/shallow";
import { sampleNearest } from "@/engines/fields/field.decode";
import { subtractFields } from "@/engines/fields/field.raster";
import { fitView, screenToCell } from "@/engines/fields/grid-view";
import { classifyZones, reductionZones } from "@/engines/fields/zones";
import { useMediaQuery } from "@/hooks/media/use-media-query";
import { useElementSize } from "@/hooks/media/use-element-size";
import { useTokenColors } from "@/hooks/theme/use-token-colors";
import { useCompareStore } from "@/stores/compare/compare.store";
import type { CompareStageProps } from "./CompareStage.types";
import { useSwipeSlider } from "./CompareStage.slider";

export interface CompareReadout {
  a: number;
  b: number;
}

/** Shared fit for both fields, ΔK and zone masks, readout of A and B under the cursor. */
export function useCompareStage(p: CompareStageProps) {
  const box = useRef<HTMLDivElement>(null);
  const size = useElementSize(box);
  const vertical = useMediaQuery("(max-width: 767px)");
  const ui = useCompareStore(useShallow((s) => ({ deltaK: s.deltaK, zones: s.zones })));
  const slider = useSwipeSlider(vertical);
  const colors = useTokenColors();
  const view = useMemo(() => fitView(p.a.cols, p.a.rows, Math.max(size.width, 1), Math.max(size.height, 1)), [p.a, size]);
  const dk = useMemo(() => (ui.deltaK ? subtractFields(p.a, p.b) : null), [ui.deltaK, p.a, p.b]);
  const t = p.thresholds;
  const codes = useMemo(() => {
    if (dk) return { a: null, b: reductionZones(dk, t.dk_reduction) };
    if (!ui.zones) return { a: null, b: null };
    return { a: classifyZones(p.a, t), b: classifyZones(p.b, t) };
  }, [dk, ui.zones, p.a, p.b, t]);
  const [readout, setReadout] = useState<CompareReadout | null>(null);
  const onPointerMove = (e: PointerEvent) => {
    const r = e.currentTarget.getBoundingClientRect();
    const [cx, cy] = screenToCell(view, p.a.rows, e.clientX - r.left, e.clientY - r.top);
    const a = sampleNearest(p.a, cx, cy);
    setReadout(Number.isFinite(a) ? { a, b: sampleNearest(p.b, cx, cy) } : null);
  };
  return { box, size, view, vertical, ...ui, slider, colors, dk, codes, readout, onPointerMove, onPointerLeave: () => setReadout(null) };
}
