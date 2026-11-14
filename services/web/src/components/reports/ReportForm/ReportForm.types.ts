import type { StudySummary } from "@/types/simulations/simulation.types";

export interface ReportFormProps {
  projectId: string;
  /** Completed or partial studies only. */
  studies: StudySummary[];
  readOnly: boolean;
}
