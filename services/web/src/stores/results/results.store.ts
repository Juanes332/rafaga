import { create } from "zustand";

export type ResultLayer = "k" | "speed" | "lawson";
export type ResultTool = "none" | "section";
export type Point = [number, number];

interface ResultsState {
  layer: ResultLayer;
  zones: boolean;
  paused: boolean;
  tool: ResultTool;
  /** Section line in local ENU metres, upwind first. */
  section: Point[];
  view3d: boolean;
  lawsonClass: string | null;
  setLayer: (layer: ResultLayer) => void;
  toggleZones: () => void;
  togglePaused: () => void;
  setTool: (tool: ResultTool) => void;
  addSectionPoint: (p: Point) => void;
  setView3d: (on: boolean) => void;
  setLawsonClass: (key: string | null) => void;
  reset: () => void;
}

const initial = { layer: "k" as ResultLayer, zones: false, paused: false, tool: "none" as ResultTool, section: [] as Point[], view3d: false, lawsonClass: null };

/** UI state of the results view (SCR-14..17). */
export const useResultsStore = create<ResultsState>()((set) => ({
  ...initial,
  setLayer: (layer) => set({ layer }),
  toggleZones: () => set((s) => ({ zones: !s.zones })),
  togglePaused: () => set((s) => ({ paused: !s.paused })),
  setTool: (tool) => set({ tool, section: [] }),
  addSectionPoint: (p) => set((s) => (s.section.length >= 2 ? s : { section: [...s.section, p] })),
  setView3d: (view3d) => set({ view3d }),
  setLawsonClass: (lawsonClass) => set({ lawsonClass }),
  reset: () => set(initial),
}));
