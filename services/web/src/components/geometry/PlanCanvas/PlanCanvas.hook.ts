import { useCallback, useState, type PointerEvent } from "react";
import { useTranslation } from "react-i18next";
import { useGeometryStore } from "@/stores/geometry/geometry.store";
import { snap } from "@/engines/geometry/polygon";
import { formatUnit } from "@/lib/format/format.number";
import { useShapeKeys } from "./PlanCanvas.keys";
import { commitMove, commitRect, useCommitShape, usePolygonTool, useRulerTool } from "./PlanCanvas.tools";
import type { Gesture, PlanCanvasProps } from "./PlanCanvas.types";
import { usePlanView, useWheelZoom } from "./PlanCanvas.view";

/** Plan editor interaction: one gesture at a time, committed to the undo stack on release. */
export function usePlanCanvas({ readOnly }: PlanCanvasProps) {
  const { t } = useTranslation();
  const view = usePlanView();
  useWheelZoom(view.svgRef);
  const tool = useGeometryStore((s) => (readOnly ? "select" : s.tool));
  const buildings = useGeometryStore((s) => s.buildings);
  const selectedId = useGeometryStore((s) => s.selectedId);
  const [gesture, setGesture] = useState<Gesture>({ kind: "none" });
  const commit = useCommitShape();
  const polygon = usePolygonTool(commit);
  const ruler = useRulerTool();
  const onShapeKey = useShapeKeys(!readOnly);

  const onShapePointerDown = useCallback(
    (id: string, e: PointerEvent<SVGGElement>) => {
      if (useGeometryStore.getState().tool !== "select" && !readOnly) return;
      e.stopPropagation();
      useGeometryStore.getState().select(id);
      if (!readOnly) setGesture({ kind: "move", id, start: view.toWorld(e, false), delta: [0, 0] });
    },
    // toWorld changes with the view box; the latest one is read at event time through the closure below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [readOnly, view.vb],
  );

  const onPointerDown = (e: PointerEvent<SVGSVGElement>) => {
    (e.currentTarget as Element).setPointerCapture?.(e.pointerId);
    const p = view.toWorld(e);
    if (tool === "rect") return setGesture({ kind: "rect", a: p, b: p });
    if (tool === "polygon") return polygon.add(p, 8 / view.ppm);
    if (tool === "ruler") return ruler.add(p);
    useGeometryStore.getState().select(null);
    setGesture({ kind: "pan", last: [e.clientX, e.clientY] });
  };

  const onPointerMove = (e: PointerEvent<SVGSVGElement>) => {
    if (tool === "polygon") polygon.setHover(view.toWorld(e));
    if (gesture.kind === "rect") setGesture({ ...gesture, b: view.toWorld(e) });
    if (gesture.kind === "move") {
      const p = view.toWorld(e, false);
      const step = useGeometryStore.getState().snapStep;
      setGesture({ ...gesture, delta: snap([p[0] - gesture.start[0], p[1] - gesture.start[1]], step) });
    }
    if (gesture.kind === "pan") {
      useGeometryStore.getState().panBy(-(e.clientX - gesture.last[0]) / view.ppm, (e.clientY - gesture.last[1]) / view.ppm);
      setGesture({ kind: "pan", last: [e.clientX, e.clientY] });
    }
  };

  const onPointerUp = () => {
    if (gesture.kind === "rect") commitRect(gesture.a, gesture.b, commit);
    if (gesture.kind === "move") commitMove(gesture.id, gesture.delta);
    setGesture({ kind: "none" });
  };

  const onKeyDown = (e: React.KeyboardEvent<SVGSVGElement>) => {
    if (e.key === "Escape") {
      polygon.cancel();
      ruler.clear();
      setGesture({ kind: "none" });
    }
    if (e.key === "Enter" && tool === "polygon") polygon.finish();
  };

  return {
    ...view,
    tool,
    buildings,
    selectedId,
    gesture,
    polygon,
    ruler,
    rulerLabel: ruler.distance != null ? t("geometry:canvas.ruler", { value: formatUnit(ruler.distance, 2, "m") }) : null,
    onShapePointerDown,
    onShapeKey,
    onPointerDown,
    onPointerMove,
    onPointerUp,
    onDoubleClick: () => tool === "polygon" && polygon.finish(),
    onKeyDown,
  };
}
