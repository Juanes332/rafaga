import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import type { Project, ProjectPatch, ProjectSummary } from "@/types/projects/project.types";

export const projectsKeys = {
  all: ["projects"] as const,
  detail: (id: string) => ["projects", id] as const,
};

export const projectsQueryOptions = () =>
  queryOptions({ queryKey: projectsKeys.all, queryFn: () => apiClient.get<ProjectSummary[]>("/projects") });

export const projectQueryOptions = (id: string) =>
  queryOptions({ queryKey: projectsKeys.detail(id), queryFn: () => apiClient.get<Project>(`/projects/${id}`) });

function useInvalidateProjects() {
  const qc = useQueryClient();
  return (project?: Project) => {
    if (project) qc.setQueryData(projectsKeys.detail(project.id), project);
    return qc.invalidateQueries({ queryKey: projectsKeys.all });
  };
}

/** POST /projects. */
export function useCreateProject() {
  const invalidate = useInvalidateProjects();
  return useMutation({
    mutationFn: (name: string) => apiClient.post<Project>("/projects", { name }),
    onSuccess: (p) => invalidate(p),
  });
}

/** PATCH /projects/{id} (name, analysis height). */
export function useUpdateProject() {
  const invalidate = useInvalidateProjects();
  return useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: ProjectPatch }) => apiClient.patch<Project>(`/projects/${id}`, patch),
    onSuccess: (p) => invalidate(p),
  });
}

/** POST /projects/{id}/duplicate. */
export function useDuplicateProject() {
  const invalidate = useInvalidateProjects();
  return useMutation({
    mutationFn: (id: string) => apiClient.post<Project>(`/projects/${id}/duplicate`),
    onSuccess: (p) => invalidate(p),
  });
}

/** DELETE /projects/{id}. */
export function useDeleteProject() {
  const invalidate = useInvalidateProjects();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/projects/${id}`),
    onSuccess: () => invalidate(),
  });
}
