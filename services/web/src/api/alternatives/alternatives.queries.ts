import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import type { Alternative, AlternativeCreate, AlternativePatch } from "@/types/alternatives/alternative.types";

export const alternativesKeys = {
  list: (projectId: string) => ["alternatives", projectId] as const,
};

/** Alternatives of a project; the base is always first. */
export const alternativesQueryOptions = (projectId: string) =>
  queryOptions({
    queryKey: alternativesKeys.list(projectId),
    queryFn: () => apiClient.get<Alternative[]>(`/projects/${projectId}/alternatives`),
  });

function useInvalidate(projectId: string) {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: alternativesKeys.list(projectId) });
}

/** POST /projects/{id}/alternatives (copy of another alternative when from_alternative_id). */
export function useCreateAlternative(projectId: string) {
  const invalidate = useInvalidate(projectId);
  return useMutation({
    mutationFn: (body: AlternativeCreate) => apiClient.post<Alternative>(`/projects/${projectId}/alternatives`, body),
    onSuccess: invalidate,
  });
}

/** PATCH /alternatives/{id}: rename or reorder. */
export function useUpdateAlternative(projectId: string) {
  const invalidate = useInvalidate(projectId);
  return useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: AlternativePatch }) => apiClient.patch<Alternative>(`/alternatives/${id}`, patch),
    onSuccess: invalidate,
  });
}

/** DELETE /alternatives/{id}; the base answers 409 base_undeletable. */
export function useDeleteAlternative(projectId: string) {
  const invalidate = useInvalidate(projectId);
  return useMutation({ mutationFn: (id: string) => apiClient.delete(`/alternatives/${id}`), onSuccess: invalidate });
}
