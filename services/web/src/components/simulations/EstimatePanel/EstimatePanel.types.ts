import type { Estimate } from "@/types/simulations/simulation.types";

export interface EstimatePanelProps {
  estimate: Estimate | undefined;
  loading: boolean;
  autoCoarsen: boolean;
  onUseProposed: (dx: number) => void;
  onAutoCoarsen: (on: boolean) => void;
}
