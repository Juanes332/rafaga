import { useQueries, useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { alternativesQueryOptions } from "@/api/alternatives/alternatives.queries";
import { studiesQueryOptions, studyQueryOptions } from "@/api/simulations/simulations.queries";
import { directionLabel } from "@/lib/format/format.direction";

export interface CompareOption {
  resultId: string;
  studyId: string;
  alternativeId: string;
  label: string;
  /** Alternative name without the wind direction. */
  name: string;
  direction: number;
  kind: string;
}

/** Every completed plan result of the project, labelled "Alternativa, E". */
export function useCompareOptions(projectId: string): { options: CompareOption[]; baseAlternativeId?: string; isLoading: boolean } {
  const { t } = useTranslation();
  const alternatives = useQuery(alternativesQueryOptions(projectId));
  const list = useQuery(studiesQueryOptions(projectId));
  const done = (list.data ?? []).filter((s) => (s.status === "completed" || s.status === "partial") && s.kind === "plan2d");
  const studies = useQueries({ queries: done.map((s) => studyQueryOptions(s.id)) });
  const options = studies.flatMap((q) => {
    const s = q.data;
    if (!s) return [];
    return s.jobs
      .filter((j) => j.status === "completed" && j.result_id && j.direction_deg != null)
      .map((j) => ({
        resultId: j.result_id as string,
        studyId: s.id,
        alternativeId: s.alternative_id,
        direction: j.direction_deg as number,
        kind: s.kind,
        name: s.alternative_name ?? "",
        label: t("compare:option", { alternative: s.alternative_name, direction: directionLabel(j.direction_deg as number) }),
      }));
  });
  const baseAlternativeId = alternatives.data?.find((a) => a.is_base)?.id;
  return { options, baseAlternativeId, isLoading: list.isLoading || alternatives.isLoading || studies.some((q) => q.isLoading) };
}

/**
 * Default pair: the base as A and another alternative simulated in the same direction as B,
 * so the strategy-effect card reads "alternativa frente a caso base". Without a simulated
 * base, the first result and the next one in the same direction.
 */
export function defaultPair(options: CompareOption[], baseAlternativeId?: string): [string, string] | null {
  for (const base of options.filter((o) => baseAlternativeId && o.alternativeId === baseAlternativeId)) {
    const alt = options.find((o) => o.alternativeId !== base.alternativeId && o.direction === base.direction);
    if (alt) return [base.resultId, alt.resultId];
  }
  const a = options[0];
  const b = options.find((o) => o.resultId !== a?.resultId && o.direction === a.direction);
  return a && b ? [a.resultId, b.resultId] : null;
}
