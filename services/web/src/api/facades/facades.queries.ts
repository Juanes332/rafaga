import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";
import { alternativesKeys } from "@/api/alternatives/alternatives.queries";
import { apiClient } from "@/lib/http/api-client";
import type {
  FacadeElement,
  FacadeElementCreate,
  FacadeElementWithAdjustments,
  FacadeStrategy,
} from "@/types/facades/facade.types";

export const facadesKeys = {
  strategies: ["facades", "strategies"] as const,
  elements: (alternativeId: string) => ["facades", "elements", alternativeId] as const,
};

/** Strategy catalogue: parameters, units, ranges, defaults, help keys. */
export const facadeStrategiesQueryOptions = () =>
  queryOptions({
    queryKey: facadesKeys.strategies,
    queryFn: () => apiClient.get<FacadeStrategy[]>("/facade-strategies"),
    staleTime: Infinity,
  });

export const facadeElementsQueryOptions = (alternativeId: string) =>
  queryOptions({
    queryKey: facadesKeys.elements(alternativeId),
    queryFn: () => apiClient.get<FacadeElement[]>(`/alternatives/${alternativeId}/facade-elements`),
  });

function useInvalidate(projectId: string, alternativeId: string) {
  const qc = useQueryClient();
  return () => {
    void qc.invalidateQueries({ queryKey: facadesKeys.elements(alternativeId) });
    return qc.invalidateQueries({ queryKey: alternativesKeys.list(projectId) });
  };
}

/** POST a strategy on a building edge; the response lists any clamped values. */
export function useCreateFacadeElement(projectId: string, alternativeId: string) {
  const invalidate = useInvalidate(projectId, alternativeId);
  return useMutation({
    mutationFn: (body: FacadeElementCreate) =>
      apiClient.post<FacadeElementWithAdjustments>(`/alternatives/${alternativeId}/facade-elements`, body),
    onSuccess: invalidate,
  });
}

/** PATCH element params; the response lists any clamped values. */
export function useUpdateFacadeElement(projectId: string, alternativeId: string) {
  const invalidate = useInvalidate(projectId, alternativeId);
  return useMutation({
    mutationFn: ({ id, params }: { id: string; params: Record<string, number | null> }) =>
      apiClient.patch<FacadeElementWithAdjustments>(`/facade-elements/${id}`, { params }),
    onSuccess: invalidate,
  });
}

export function useDeleteFacadeElement(projectId: string, alternativeId: string) {
  const invalidate = useInvalidate(projectId, alternativeId);
  return useMutation({ mutationFn: (id: string) => apiClient.delete(`/facade-elements/${id}`), onSuccess: invalidate });
}
