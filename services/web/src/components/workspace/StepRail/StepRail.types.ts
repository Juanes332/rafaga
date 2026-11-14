export type StepKey = "location" | "geometry" | "wind" | "alternatives" | "simulate" | "compare";
export type StepState = "done" | "current" | "todo" | "locked";

export interface StepFacts {
  hasLocation: boolean;
  buildingCount: number;
  hasWind: boolean;
  alternativeCount: number;
  completedStudies: number;
  current: StepKey | null;
}

export interface StepItem {
  key: StepKey;
  index: number;
  state: StepState;
  /** i18n key of the one-line lock reason. */
  reasonKey: string | null;
}

export interface StepRailProps {
  projectId: string;
}
