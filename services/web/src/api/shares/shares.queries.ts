import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import type { Share } from "@/types/users/user.types";

export const sharesKeys = { list: (projectId: string) => ["shares", projectId] as const };

/** Who can see a project besides its owner. */
export const sharesQueryOptions = (projectId: string) =>
  queryOptions({
    queryKey: sharesKeys.list(projectId),
    queryFn: () => apiClient.get<Share[]>(`/projects/${projectId}/shares`),
  });

interface ShareTarget {
  projectId: string;
  userId: string;
}

/** PUT (grant) or DELETE (revoke) /projects/{id}/shares/{user_id}. */
export function useToggleShare() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, userId, grant }: ShareTarget & { grant: boolean }) =>
      grant
        ? apiClient.put<void>(`/projects/${projectId}/shares/${userId}`, {})
        : apiClient.delete(`/projects/${projectId}/shares/${userId}`),
    onSuccess: (_d, v) => qc.invalidateQueries({ queryKey: sharesKeys.list(v.projectId) }),
  });
}
