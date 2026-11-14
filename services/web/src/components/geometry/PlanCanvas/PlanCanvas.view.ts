import { useEffect, useMemo, useRef, useState, type RefObject } from "react";
import { bbox, snap } from "@/engines/geometry/polygon";
import { useGeometryStore } from "@/stores/geometry/geometry.store";
import { clientToWorld, computeViewBox, pxPerMetre, type ViewBox } from "./PlanCanvas.utils";
import type { ToWorld } from "./PlanCanvas.types";

interface PlanView {
  svgRef: RefObject<SVGSVGElement | null>;
  vb: ViewBox;
  ppm: number;
  toWorld: ToWorld;
}

/** Fits the view to the buildings once per load; zoom/pan come from the store. */
export function usePlanView(): PlanView {
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [size, setSize] = useState({ width: 800, height: 600 });
  const buildings = useGeometryStore((s) => s.buildings);
  const projectId = useGeometryStore((s) => s.projectId);
  const baseVersion = useGeometryStore((s) => s.baseVersion);
  const zoom = useGeometryStore((s) => s.zoom);
  const pan = useGeometryStore((s) => s.pan);
  const snapStep = useGeometryStore((s) => s.snapStep);
  // Refit only on (re)load, not on every edit: the plan must not jump while drawing.
  const content = useMemo(
    () => (buildings.length ? bbox(buildings.map((b) => b.footprint)) : null),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [projectId, baseVersion, buildings.length === 0],
  );
  const aspect = size.width / size.height;
  const vb = useMemo(() => computeViewBox(content, zoom, pan, aspect), [content, zoom, pan, aspect]);
  useResizeObserver(svgRef, setSize);
  const rect = () => svgRef.current?.getBoundingClientRect() ?? { left: 0, top: 0, width: size.width, height: size.height };
  const toWorld: ToWorld = (e, snapped = true) => {
    const p = clientToWorld(e.clientX, e.clientY, rect(), vb);
    return snapped ? snap(p, snapStep) : p;
  };
  return { svgRef, vb, ppm: pxPerMetre({ left: 0, top: 0, ...size }, vb), toWorld };
}

function useResizeObserver(ref: RefObject<SVGSVGElement | null>, onSize: (s: { width: number; height: number }) => void): void {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      if (width > 0 && height > 0) onSize({ width, height });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [ref, onSize]);
}

/** Wheel zoom needs a non-passive native listener to stop the page scrolling. */
export function useWheelZoom(ref: RefObject<SVGSVGElement | null>): void {
  const zoomBy = useGeometryStore((s) => s.zoomBy);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      zoomBy(e.deltaY < 0 ? 1.15 : 1 / 1.15);
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, [ref, zoomBy]);
}
