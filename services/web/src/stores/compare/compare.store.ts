import { create } from "zustand";

interface CompareState {
  /** Swipe handle position, 0–100 % from the left (or top on phones). */
  position: number;
  deltaK: boolean;
  zones: boolean;
  setPosition: (p: number) => void;
  toggleDeltaK: () => void;
  toggleZones: () => void;
  reset: () => void;
}

const clamp = (p: number) => Math.max(0, Math.min(100, p));

/** Keyboard model of the comparator slider: arrows 2 %, Shift+arrows 10 %, Home/End. */
export function nextPosition(pos: number, key: string, shift: boolean): number {
  const step = shift ? 10 : 2;
  if (key === "ArrowRight" || key === "ArrowUp") return clamp(pos + step);
  if (key === "ArrowLeft" || key === "ArrowDown") return clamp(pos - step);
  if (key === "Home") return 0;
  if (key === "End") return 100;
  return pos;
}

/** UI state of the full-screen comparison (SCR-18). */
export const useCompareStore = create<CompareState>()((set) => ({
  position: 50,
  deltaK: false,
  zones: false,
  setPosition: (p) => set({ position: clamp(p) }),
  toggleDeltaK: () => set((s) => ({ deltaK: !s.deltaK })),
  toggleZones: () => set((s) => ({ zones: !s.zones })),
  reset: () => set({ position: 50, deltaK: false, zones: false }),
}));
