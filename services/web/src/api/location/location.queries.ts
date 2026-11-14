import { useMutation, useQueryClient } from "@tanstack/react-query";
import { projectsKeys } from "@/api/projects/projects.queries";
import { windKeys } from "@/api/wind/wind.queries";
import { apiClient } from "@/lib/http/api-client";
import type { LocationRequest, Project } from "@/types/projects/project.types";

/** PUT /projects/{id}/location; elevation_m only when the user typed it (manual fallback). */
export function useSetLocation(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: LocationRequest) => apiClient.put<Project>(`/projects/${projectId}/location`, body),
    onSuccess: (project) => {
      qc.setQueryData(projectsKeys.detail(projectId), project);
      void qc.invalidateQueries({ queryKey: projectsKeys.all });
      // The site climate depends on the coordinates.
      void qc.invalidateQueries({ queryKey: windKeys.detail(projectId) });
    },
  });
}
