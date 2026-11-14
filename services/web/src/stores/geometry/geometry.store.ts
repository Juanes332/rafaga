import { create } from "zustand";
import type { Building, Geometry } from "@/types/geometry/geometry.types";

/** Undo depth; the contract asks for ≥50. */
export const HISTORY_LIMIT = 100;

export type EditorTool = "select" | "rect" | "polygon" | "ruler";
export type EditorView = "plan" | "3d";

interface GeometryEditorState {
  projectId: string | null;
  baseVersion: number;
  buildings: Building[];
  past: Building[][];
  future: Building[][];
  dirty: boolean;
  selectedId: string | null;
  tool: EditorTool;
  view: EditorView;
  snapStep: number;
  /** View transform: zoom 1 = fit content; pan in metres. */
  zoom: number;
  pan: [number, number];
  load: (projectId: string, geometry: Geometry) => void;
  apply: (next: Building[]) => void;
  undo: () => void;
  redo: () => void;
  select: (id: string | null) => void;
  setTool: (tool: EditorTool) => void;
  setView: (view: EditorView) => void;
  setSnap: (step: number) => void;
  markSaved: (version: number) => void;
  zoomBy: (factor: number) => void;
  panBy: (dx: number, dy: number) => void;
  resetView: () => void;
}

export const ZOOM_RANGE: readonly [number, number] = [0.25, 20];

function keepSelection(selectedId: string | null, buildings: Building[]): string | null {
  return selectedId && buildings.some((b) => b.id === selectedId) ? selectedId : null;
}

/** Geometry draft with a snapshot undo stack; the server copy lives in Query. */
export const useGeometryStore = create<GeometryEditorState>()((set, get) => ({
  projectId: null,
  baseVersion: 1,
  buildings: [],
  past: [],
  future: [],
  dirty: false,
  selectedId: null,
  tool: "select",
  view: "plan",
  snapStep: 1,
  zoom: 1,
  pan: [0, 0],
  load: (projectId, g) =>
    set((s) => ({
      projectId,
      baseVersion: g.version,
      buildings: g.buildings,
      past: [],
      future: [],
      dirty: false,
      selectedId: null,
      zoom: 1,
      pan: [0, 0],
      // A different project starts in the plan with the selection tool.
      ...(s.projectId === projectId ? {} : { tool: "select" as const, view: "plan" as const }),
    })),
  apply: (next) =>
    set((s) => ({ buildings: next, past: [...s.past, s.buildings].slice(-HISTORY_LIMIT), future: [], dirty: true })),
  undo: () => {
    const { past, buildings, future, selectedId } = get();
    const prev = past.at(-1);
    if (!prev) return;
    set({ buildings: prev, past: past.slice(0, -1), future: [buildings, ...future], dirty: true, selectedId: keepSelection(selectedId, prev) });
  },
  redo: () => {
    const { past, buildings, future, selectedId } = get();
    const next = future[0];
    if (!next) return;
    set({ buildings: next, past: [...past, buildings], future: future.slice(1), dirty: true, selectedId: keepSelection(selectedId, next) });
  },
  select: (id) => set({ selectedId: id }),
  setTool: (tool) => set((s) => ({ tool, selectedId: tool === "select" ? s.selectedId : null })),
  setView: (view) => set({ view }),
  setSnap: (snapStep) => set({ snapStep }),
  markSaved: (version) => set({ baseVersion: version, dirty: false }),
  zoomBy: (factor) => set((s) => ({ zoom: Math.min(ZOOM_RANGE[1], Math.max(ZOOM_RANGE[0], s.zoom * factor)) })),
  panBy: (dx, dy) => set((s) => ({ pan: [s.pan[0] + dx, s.pan[1] + dy] })),
  resetView: () => set({ zoom: 1, pan: [0, 0] }),
}));
