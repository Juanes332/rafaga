import { queryOptions } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import type { SceneView } from "@/types/scene/scene-view.types";

export const sceneKeys = { detail: (alternativeId: string) => ["scene", alternativeId] as const };

/** Compiled canonical scene of an alternative (solids + porous zones). */
export const sceneQueryOptions = (alternativeId: string) =>
  queryOptions({
    queryKey: sceneKeys.detail(alternativeId),
    queryFn: () => apiClient.get<SceneView>(`/alternatives/${alternativeId}/scene`),
  });
