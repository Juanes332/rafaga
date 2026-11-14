import { useRef, type KeyboardEvent, type PointerEvent } from "react";
import { useCompareStore, nextPosition } from "@/stores/compare/compare.store";

/** Swipe handle: drag anywhere along the axis, arrows 2 %, Shift+arrows 10 %. */
export function useSwipeSlider(vertical: boolean) {
  const position = useCompareStore((s) => s.position);
  const setPosition = useCompareStore((s) => s.setPosition);
  const dragging = useRef(false);
  const fromPointer = (e: PointerEvent) => {
    const r = (e.currentTarget.parentElement ?? e.currentTarget).getBoundingClientRect();
    const t = vertical ? (e.clientY - r.top) / Math.max(r.height, 1) : (e.clientX - r.left) / Math.max(r.width, 1);
    setPosition(t * 100);
  };
  return {
    position,
    onKeyDown: (e: KeyboardEvent) => {
      const next = nextPosition(position, e.key, e.shiftKey);
      if (next === position && !e.key.startsWith("Arrow")) return;
      e.preventDefault();
      setPosition(next);
    },
    onPointerDown: (e: PointerEvent) => {
      dragging.current = true;
      e.currentTarget.setPointerCapture?.(e.pointerId);
    },
    onPointerMove: (e: PointerEvent) => dragging.current && fromPointer(e),
    onPointerUp: () => {
      dragging.current = false;
    },
  };
}
