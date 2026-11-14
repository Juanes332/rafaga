import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { alternativesQueryOptions } from "@/api/alternatives/alternatives.queries";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { useCreateReport } from "@/api/reports/reports.queries";
import type { ReportFormProps } from "./ReportForm.types";

/** Studies to include (all by default), a baseline among them, and the comfort toggle. */
/** The base case is the natural reference; StudySummary has no is_base, so match by alternative name. */
function defaultBaseline(studies: ReportFormProps["studies"], baseName: string | undefined): string {
  return (studies.find((s) => s.alternative_name === baseName) ?? studies[0])?.id ?? "";
}

export function useReportForm({ projectId, studies }: ReportFormProps) {
  const { t } = useTranslation();
  const [selected, setSelected] = useState<string[]>([]);
  const [baseline, setBaseline] = useState("");
  const [comfort, setComfort] = useState(true);
  const create = useCreateReport(projectId);
  const alternatives = useQuery(alternativesQueryOptions(projectId));
  const baseName = alternatives.data?.find((a) => a.is_base)?.name;
  const ids = studies.map((s) => s.id).join(",");
  useEffect(() => {
    setSelected(ids ? ids.split(",") : []);
    setBaseline(defaultBaseline(studies, baseName));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ids, baseName]);

  const toggle = (id: string, on: boolean) => {
    const next = on ? studies.map((s) => s.id).filter((x) => x === id || selected.includes(x)) : selected.filter((x) => x !== id);
    setSelected(next);
    if (!next.includes(baseline)) setBaseline(defaultBaseline(studies.filter((s) => next.includes(s.id)), baseName));
  };
  const onSubmit = () =>
    create.mutate(
      { study_ids: selected, baseline_study_id: baseline || undefined, include_comfort: comfort },
      { onSuccess: () => toast(t("reports:toast.queued")) },
    );
  return {
    selected,
    baseline,
    comfort,
    toggle,
    setBaseline,
    setComfort,
    onSubmit,
    canSubmit: selected.length > 0 && !create.isPending,
    pending: create.isPending,
    error: create.error,
  };
}
