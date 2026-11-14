import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import { isApiError } from "@/lib/http/api-error";
import type { TerrainCategory, WindClimate, WindPatch } from "@/types/wind/wind.types";

export const windKeys = {
  detail: (projectId: string) => ["wind", projectId] as const,
  terrain: ["wind", "terrain-categories"] as const,
};

/** Site wind climate; null while none has been set (404). */
export const windQueryOptions = (projectId: string) =>
  queryOptions({
    queryKey: windKeys.detail(projectId),
    queryFn: async (): Promise<WindClimate | null> => {
      try {
        return await apiClient.get<WindClimate>(`/projects/${projectId}/wind`);
      } catch (error) {
        if (isApiError(error) && error.status === 404) return null;
        throw error;
      }
    },
  });

/** Terrain categories with their z0 (BR-08). */
export const terrainCategoriesQueryOptions = () =>
  queryOptions({
    queryKey: windKeys.terrain,
    queryFn: () => apiClient.get<TerrainCategory[]>("/terrain-categories"),
    staleTime: Infinity,
  });

function useStoreWind(projectId: string) {
  const qc = useQueryClient();
  return (wind: WindClimate) => qc.setQueryData(windKeys.detail(projectId), wind);
}

/** POST /projects/{id}/wind/era5: 10 years of hourly ERA5 → 16-sector rose. */
export function useFetchEra5(projectId: string) {
  const store = useStoreWind(projectId);
  return useMutation({
    mutationFn: (years: number = 10) => apiClient.post<WindClimate>(`/projects/${projectId}/wind/era5`, { years }),
    onSuccess: store,
  });
}

/** PATCH /projects/{id}/wind: terrain, z0, manual direction and speed. */
export function useUpdateWind(projectId: string) {
  const store = useStoreWind(projectId);
  return useMutation({
    mutationFn: (patch: WindPatch) => apiClient.patch<WindClimate>(`/projects/${projectId}/wind`, patch),
    onSuccess: store,
  });
}
