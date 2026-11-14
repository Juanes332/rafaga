import { queryOptions } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import type { ComparisonAreas, ComparisonCheck, ComparisonComfort } from "@/types/comparisons/comparison.types";
import type { Thresholds } from "@/types/settings/settings.types";

export const comparisonsKeys = {
  check: (a: string, b: string) => ["comparisons", "check", a, b] as const,
  areas: (a: string, b: string, t: Thresholds) => ["comparisons", "areas", a, b, t.k_accel, t.k_stagnation, t.dk_reduction] as const,
  comfort: (a: string, b: string) => ["comparisons", "comfort", a, b] as const,
};

/** BR-11: are two results on the same grid, direction and parameters? */
export const comparisonCheckQueryOptions = (a: string, b: string) =>
  queryOptions({
    queryKey: comparisonsKeys.check(a, b),
    queryFn: () => apiClient.get<ComparisonCheck>("/comparisons/check", { query: { a, b } }),
  });

/** Zone areas for A, B and the reduction (ΔK) zone. */
export const comparisonAreasQueryOptions = (a: string, b: string, t: Thresholds) =>
  queryOptions({
    queryKey: comparisonsKeys.areas(a, b, t),
    queryFn: () =>
      apiClient.get<ComparisonAreas>("/comparisons/areas", {
        query: { a, b, k_accel: t.k_accel, k_stagnation: t.k_stagnation, dk_reduction: t.dk_reduction },
      }),
  });

/** Lawson class areas of the two studies. */
export const comparisonComfortQueryOptions = (studyA: string, studyB: string) =>
  queryOptions({
    queryKey: comparisonsKeys.comfort(studyA, studyB),
    queryFn: () => apiClient.get<ComparisonComfort>("/comparisons/comfort", { query: { study_a: studyA, study_b: studyB } }),
  });
