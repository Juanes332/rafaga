import { useCallback, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { fetchReportFile, reportsQueryOptions } from "@/api/reports/reports.queries";
import { studiesQueryOptions } from "@/api/simulations/simulations.queries";
import { useProjectAccess } from "@/hooks/access/use-project-access";
import { saveBlob } from "@/hooks/download/save-blob";
import type { Report } from "@/types/exports/export.types";

const DONE = new Set(["completed", "partial"]);

/** SCR-20: completed studies feed the form; versions poll while one is generating. */
export function useReportsScreen() {
  const { projectId } = useParams({ strict: false }) as { projectId: string };
  const { readOnly } = useProjectAccess(projectId);
  const studies = useQuery(studiesQueryOptions(projectId));
  const reports = useQuery(reportsQueryOptions(projectId));
  const [downloadError, setDownloadError] = useState<unknown>(null);
  const done = (studies.data ?? []).filter((s) => DONE.has(s.status));

  const onDownload = useCallback(async (r: Report) => {
    try {
      setDownloadError(null);
      saveBlob(await fetchReportFile(r.id), `rafaga-informe-v${r.version}.pdf`);
    } catch (e) {
      setDownloadError(e);
    }
  }, []);

  return {
    projectId,
    readOnly,
    studies: done,
    loading: studies.isLoading || reports.isLoading,
    reports: reports.data ?? [],
    error: reports.error ?? studies.error ?? downloadError,
    onDownload: (r: Report) => void onDownload(r),
  };
}
