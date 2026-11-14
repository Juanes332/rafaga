import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import type { Report, ReportAccepted, ReportCreate } from "@/types/exports/export.types";

export const reportsKeys = { list: (projectId: string) => ["reports", projectId] as const };

const ACTIVE = new Set(["queued", "running"]);

export function anyReportActive(list: Report[] | undefined): boolean {
  return (list ?? []).some((r) => ACTIVE.has(r.status));
}

/** Report versions of a project; polled every 1 s while one is being generated. */
export const reportsQueryOptions = (projectId: string) =>
  queryOptions({
    queryKey: reportsKeys.list(projectId),
    queryFn: () => apiClient.get<Report[]>(`/projects/${projectId}/reports`),
    refetchInterval: (q) => (anyReportActive(q.state.data) ? 1_000 : false),
  });

/** PDF bytes with the bearer header. */
export const fetchReportFile = (id: string) => apiClient.blob(`/reports/${id}/file`);

/** POST /projects/{id}/reports, then refresh the version list. */
export function useCreateReport(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ReportCreate) => apiClient.post<ReportAccepted>(`/projects/${projectId}/reports`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: reportsKeys.list(projectId) }),
  });
}
