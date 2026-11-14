import type { TFunction } from "i18next";
import { directionLabel } from "@/lib/format/format.direction";
import { formatDuration } from "@/lib/format/format.date";
import { formatPercent } from "@/lib/format/format.number";
import { jobErrorMessage } from "@/lib/http/error-copy";
import type { Job } from "@/types/simulations/simulation.types";

export interface JobRow {
  id: string;
  dir: string;
  statusText: string;
  percent: number;
  percentText: string;
  detail: string;
  error: string | null;
  canCancel: boolean;
  canRetry: boolean;
  resultId: string | null;
}

function detailOf(job: Job, t: TFunction): string {
  if (job.status !== "running") return "";
  const parts = [
    job.phase ? t(`simulate:jobs.phase.${job.phase}`, { defaultValue: "" }) : "",
    job.eta_seconds != null ? t("simulate:jobs.eta", { value: formatDuration(job.eta_seconds) }) : "",
    job.device_used ? t("simulate:jobs.device", { device: job.device_used.toUpperCase() }) : "",
  ];
  return parts.filter(Boolean).join(". ");
}

/** Plain-language view of one job: direction, status, progress, phase/ETA/device, error + fix. */
export function jobRow(job: Job, t: TFunction): JobRow {
  const dir = job.direction_deg != null ? directionLabel(job.direction_deg) : t("simulate:form.kinds.section2d");
  return {
    id: job.id,
    dir,
    statusText: t(`simulate:jobs.status.${job.status}`),
    percent: Math.round(job.progress * 100),
    percentText: formatPercent(job.progress, 0),
    detail: detailOf(job, t),
    error: job.status === "failed" ? jobErrorMessage(job.error?.code) : null,
    canCancel: job.status === "queued" || job.status === "running",
    canRetry: job.status === "failed" && job.resumable,
    resultId: job.status === "completed" ? (job.result_id ?? null) : null,
  };
}
