import { useQuery } from "@tanstack/react-query";
import { useShallow } from "zustand/react/shallow";
import { comfortQueryOptions, useRecomputeComfort } from "@/api/results/comfort.queries";
import { useResultsStore } from "@/stores/results/results.store";
import type { Comfort } from "@/types/results/result.types";

interface UseLawsonPanel {
  comfort: Comfort | undefined;
  error: unknown;
  selected: string | null;
  select: (key: string | null) => void;
  recompute: () => void;
  recomputing: boolean;
  recomputeError: unknown;
}

/** SCR-15: comfort of the study, class selection and recompute after a Lawson table change. */
export function useLawsonPanel(studyId: string): UseLawsonPanel {
  const query = useQuery(comfortQueryOptions(studyId));
  const mutation = useRecomputeComfort(studyId);
  const { selected, select } = useResultsStore(useShallow((s) => ({ selected: s.lawsonClass, select: s.setLawsonClass })));
  return {
    comfort: query.data,
    error: query.error,
    selected,
    select: (key) => select(key === selected ? null : key),
    recompute: () => mutation.mutate(),
    recomputing: mutation.isPending || query.data?.status === "running" || query.data?.status === "pending",
    recomputeError: mutation.error,
  };
}
