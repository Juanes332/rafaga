import { useQuery } from "@tanstack/react-query";
import { studiesQueryOptions } from "@/api/simulations/simulations.queries";
import type { StudySummary } from "@/types/simulations/simulation.types";

const DONE = new Set(["completed", "partial"]);

/** Study list, polled every 3 s while this list is on screen (ADR-07). */
export function useJobsList(projectId: string): { studies: StudySummary[]; loading: boolean; canCompare: boolean; error: unknown } {
  const q = useQuery(studiesQueryOptions(projectId, true));
  const studies = q.data ?? [];
  return { studies, loading: q.isLoading, canCompare: studies.filter((s) => DONE.has(s.status)).length >= 2, error: q.error };
}
