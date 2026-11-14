import { queryOptions, useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import type { Export, ExportAccepted, ExportCreate } from "@/types/exports/export.types";

export const exportsKeys = { detail: (id: string) => ["exports", id] as const };

const ACTIVE = new Set(["queued", "running"]);

export function isExportActive(e: Pick<Export, "status"> | undefined): boolean {
  return e !== undefined && ACTIVE.has(e.status);
}

/** Export status; polled every 1 s until terminal (ADR-07). */
export const exportQueryOptions = (id: string) =>
  queryOptions({
    queryKey: exportsKeys.detail(id),
    queryFn: () => apiClient.get<Export>(`/exports/${id}`),
    refetchInterval: (q) => (q.state.data === undefined || isExportActive(q.state.data) ? 1_000 : false),
  });

/** PNG bytes, fetched with the bearer header (never a token in a URL). */
export const fetchExportFile = (id: string) => apiClient.blob(`/exports/${id}/file`);

/** POST /exports. */
export function useCreateExport() {
  return useMutation({ mutationFn: (body: ExportCreate) => apiClient.post<ExportAccepted>("/exports", body) });
}
