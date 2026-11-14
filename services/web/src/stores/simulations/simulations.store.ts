import { create } from "zustand";

export type SimKind = "plan2d" | "section2d" | "volume3d";
export type SimDevice = "auto" | "cpu" | "gpu";

interface FormFields {
  projectId: string | null;
  alternativeId: string | null;
  kind: SimKind;
  directions: number[];
  dxM: number;
  device: SimDevice;
  autoCoarsen: boolean;
}

interface SimulationFormState extends FormFields {
  forProject: (projectId: string) => void;
  setAlternative: (id: string) => void;
  setKind: (kind: SimKind) => void;
  toggleDirection: (deg: number) => void;
  setDirections: (degs: number[]) => void;
  setDx: (dx: number) => void;
  setDevice: (device: SimDevice) => void;
  setAutoCoarsen: (on: boolean) => void;
}

const INITIAL: Omit<FormFields, "projectId"> = {
  alternativeId: null,
  kind: "plan2d",
  directions: [],
  dxM: 1,
  device: "auto",
  autoCoarsen: false,
};

/** Step 5 form, shared by the direction rose (canvas) and the form (inspector). */
export const useSimulationFormStore = create<SimulationFormState>()((set, get) => ({
  projectId: null,
  ...INITIAL,
  forProject: (projectId) => {
    if (get().projectId !== projectId) set({ projectId, ...INITIAL });
  },
  setAlternative: (alternativeId) => set({ alternativeId }),
  setKind: (kind) => set({ kind }),
  toggleDirection: (deg) =>
    set((s) => ({
      directions: s.directions.includes(deg) ? s.directions.filter((d) => d !== deg) : [...s.directions, deg].sort((a, b) => a - b),
    })),
  setDirections: (degs) => set({ directions: [...degs].sort((a, b) => a - b) }),
  setDx: (dxM) => set({ dxM, autoCoarsen: false }),
  setDevice: (device) => set({ device }),
  setAutoCoarsen: (autoCoarsen) => set({ autoCoarsen }),
}));
