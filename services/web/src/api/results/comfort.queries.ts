import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import type { Comfort } from "@/types/results/result.types";

export const comfortKeys = { study: (studyId: string) => ["comfort", studyId] as const };

/** Lawson comfort of a study for the caller's current table; polls while recomputing. */
export const comfortQueryOptions = (studyId: string) =>
  queryOptions({
    queryKey: comfortKeys.study(studyId),
    queryFn: () => apiClient.get<Comfort>(`/simulations/${studyId}/comfort`),
    refetchInterval: (q) => (q.state.data && (q.state.data.status === "pending" || q.state.data.status === "running") ? 1_000 : false),
  });

/** POST …/comfort/recompute after the Lawson table changed in Ajustes. */
export function useRecomputeComfort(studyId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<Comfort>(`/simulations/${studyId}/comfort/recompute`),
    onSuccess: (data) => {
      qc.setQueryData(comfortKeys.study(studyId), data);
      return qc.invalidateQueries({ queryKey: comfortKeys.study(studyId) });
    },
  });
}
