import { create } from "zustand";

export interface EdgeRef {
  buildingId: string;
  edgeIndex: number;
}

interface FacadesState {
  alternativeId: string | null;
  edge: EdgeRef | null;
  selectAlternative: (id: string) => void;
  selectEdge: (edge: EdgeRef | null) => void;
  reset: () => void;
}

const sameEdge = (a: EdgeRef | null, b: EdgeRef | null) => a !== null && b !== null && a.buildingId === b.buildingId && a.edgeIndex === b.edgeIndex;

/** Step 4 UI selection: which alternative is open and which façade edge is picked. */
export const useFacadesStore = create<FacadesState>()((set) => ({
  alternativeId: null,
  edge: null,
  selectAlternative: (id) => set({ alternativeId: id, edge: null }),
  selectEdge: (edge) => set((s) => ({ edge: sameEdge(s.edge, edge) ? null : edge })),
  reset: () => set({ alternativeId: null, edge: null }),
}));
