import type { SimKind } from "@/stores/simulations/simulations.store";
import type { Estimate } from "@/types/simulations/simulation.types";

/** 3D on CPU takes hours (about 6 MLUPS against ~880 on GPU), so it needs an explicit yes. */
export function needsCpuConfirmation(kind: SimKind, estimate: Estimate | undefined): boolean {
  if (!estimate || kind !== "volume3d") return false;
  // With the solver offline the device is a guess, not a fact
  return estimate.device === "cpu" && estimate.rejected_reason !== "solver_offline";
}

/** NFR-03: reference node limit of a 3D run on CPU (90 min at <= 3 M nodes). */
export const NFR03_CPU_MAX_NODES = 3_000_000;

/** The solver heartbeat is gone, so any launch would only queue behind nothing. */
export function isSolverOffline(estimate: Estimate | undefined): boolean {
  return estimate?.rejected_reason === "solver_offline";
}
