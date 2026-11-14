import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import type { WindClimate } from "@/types/wind/wind.types";
import type { FacadeStrategy } from "@/types/facades/facade.types";
import type { Template, TemplateCreate } from "@/types/settings/settings.types";

export const templatesKeys = {
  all: ["templates"] as const,
};

export const templatesQueryOptions = () =>
  queryOptions({ queryKey: templatesKeys.all, queryFn: () => apiClient.get<Template[]>("/templates") });

/** Strategy defaults keyed by type, the shape stored in a template's facade_defaults. */
export function facadeDefaultsFrom(strategies: FacadeStrategy[]): Record<string, Record<string, number | null>> {
  return Object.fromEntries(
    strategies.map((s) => [s.type, Object.fromEntries(s.parameters.map((p) => [p.key, p.default ?? null]))]),
  );
}

/** POST /templates. */
export function useCreateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: TemplateCreate) => apiClient.post<Template>("/templates", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: templatesKeys.all }),
  });
}

/** DELETE /templates/{id}. */
export function useDeleteTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/templates/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: templatesKeys.all }),
  });
}

/** POST /projects/{id}/apply-template; the project's wind climate changes. */
export function useApplyTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, templateId }: { projectId: string; templateId: string }) =>
      apiClient.post<WindClimate>(`/projects/${projectId}/apply-template`, { template_id: templateId }),
    onSuccess: (_w, v) => qc.invalidateQueries({ queryKey: ["wind", v.projectId] }),
  });
}
