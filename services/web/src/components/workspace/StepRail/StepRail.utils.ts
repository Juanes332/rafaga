import type { StepFacts, StepItem, StepKey } from "./StepRail.types";

export const STEP_ORDER: StepKey[] = ["location", "geometry", "wind", "alternatives", "simulate", "compare"];

function isDone(key: StepKey, f: StepFacts): boolean {
  switch (key) {
    case "location":
      return f.hasLocation;
    case "geometry":
      return f.buildingCount > 0;
    case "wind":
      return f.hasWind;
    case "alternatives":
      return f.alternativeCount > 1;
    case "simulate":
      return f.completedStudies > 0;
    default:
      return false;
  }
}

function lockReason(key: StepKey, f: StepFacts): string | null {
  if ((key === "wind" || key === "simulate") && !f.hasLocation) return "workspace:steps.lockedLocation";
  if (key === "compare" && f.completedStudies < 2) return "workspace:steps.lockedResults";
  return null;
}

/** Derive each step's state: locks come first, then current, then completion. */
export function computeSteps(f: StepFacts): StepItem[] {
  return STEP_ORDER.map((key, i) => {
    const reasonKey = lockReason(key, f);
    const state = reasonKey ? "locked" : key === f.current ? "current" : isDone(key, f) ? "done" : "todo";
    return { key, index: i + 1, state, reasonKey };
  });
}

/** Which step a pathname belongs to; results and reports live under "simulate". */
export function stepFromPath(pathname: string): StepKey | null {
  const seg = pathname.split("/")[3];
  if (seg === "results" || seg === "reports") return "simulate";
  return STEP_ORDER.includes(seg as StepKey) ? (seg as StepKey) : null;
}
