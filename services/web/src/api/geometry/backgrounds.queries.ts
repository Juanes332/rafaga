import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import type { BackgroundPatch, BackgroundPlan } from "@/types/geometry/geometry.types";
import { geometryKeys } from "./geometry.queries";

/** Trace plans are capped at 25 MB server-side; checked before upload too. */
export const BACKGROUND_MAX_BYTES = 25 * 1024 * 1024;

export const backgroundsQueryOptions = (projectId: string) =>
  queryOptions({
    queryKey: geometryKeys.backgrounds(projectId),
    queryFn: () => apiClient.get<BackgroundPlan[]>(`/projects/${projectId}/backgrounds`),
  });

/** Rendered page as an object URL: images go through fetch + token, never a token in a URL. */
export const backgroundPageQueryOptions = (backgroundId: string, page: number) =>
  queryOptions({
    queryKey: ["backgrounds", backgroundId, "page", page] as const,
    queryFn: async () => URL.createObjectURL(await apiClient.blob(`/backgrounds/${backgroundId}/pages/${page}.png`)),
    staleTime: Infinity,
  });

/** POST /backgrounds (multipart image or PDF). */
export function useUploadBackground(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return apiClient.upload<BackgroundPlan>(`/projects/${projectId}/backgrounds`, form);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: geometryKeys.backgrounds(projectId) }),
  });
}

/** PATCH /backgrounds/{id}: page, calibration, transform, opacity. */
export function useUpdateBackground(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: BackgroundPatch }) => apiClient.patch<BackgroundPlan>(`/backgrounds/${id}`, patch),
    onSuccess: () => qc.invalidateQueries({ queryKey: geometryKeys.backgrounds(projectId) }),
  });
}

/** DELETE /backgrounds/{id}. */
export function useDeleteBackground(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/backgrounds/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: geometryKeys.backgrounds(projectId) }),
  });
}
