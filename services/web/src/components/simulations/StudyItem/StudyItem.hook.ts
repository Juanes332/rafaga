import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { isStudyActive, studyQueryOptions, useCancelJob, useCancelStudy, useRetryJob } from "@/api/simulations/simulations.queries";
import { formatRelative } from "@/lib/format/format.date";
import type { StudySummary } from "@/types/simulations/simulation.types";
import { jobRow, type JobRow } from "./StudyItem.utils";

interface UseStudyItem {
  title: string;
  statusText: string;
  when: string;
  active: boolean;
  jobs: JobRow[];
  error: unknown;
  onCancelStudy: () => void;
  onCancelJob: (id: string) => void;
  onRetry: (id: string) => void;
}

/** One study, polled every second while any job is active (ADR-07); survives reloads. */
export function useStudyItem(projectId: string, summary: StudySummary): UseStudyItem {
  const { t } = useTranslation();
  const study = useQuery(studyQueryOptions(summary.id));
  const cancelStudy = useCancelStudy(projectId);
  const cancelJob = useCancelJob(projectId);
  const retry = useRetryJob(projectId);
  const s = study.data;
  return {
    title: t("simulate:jobs.study", {
      alternative: s?.alternative_name ?? summary.alternative_name,
      kind: t(`simulate:form.kinds.${s?.kind ?? summary.kind}`),
    }),
    statusText: t(`simulate:jobs.status.${s?.status ?? summary.status}`),
    when: t("simulate:jobs.createdAt", { when: formatRelative(s?.created_at ?? summary.created_at ?? "") }),
    active: isStudyActive(s),
    jobs: (s?.jobs ?? []).map((j) => jobRow(j, t)),
    error: study.error ?? cancelStudy.error ?? cancelJob.error ?? retry.error,
    onCancelStudy: () => cancelStudy.mutate(summary.id, { onSuccess: () => toast(t("simulate:jobs.cancelled")) }),
    onCancelJob: (id) => cancelJob.mutate(id),
    onRetry: (id) => retry.mutate(id),
  };
}
