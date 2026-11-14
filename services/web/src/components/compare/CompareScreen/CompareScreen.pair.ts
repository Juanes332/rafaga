import { useEffect } from "react";
import { useNavigate, useParams, useSearch } from "@tanstack/react-router";
import type { CompareSearch } from "@/app/routes.workspace";
import { defaultPair, useCompareOptions, type CompareOption } from "./CompareScreen.options";

/** A/B selection lives in the URL (?a=&b=) so a comparison can be bookmarked. */
export function useComparePair() {
  const { projectId } = useParams({ strict: false }) as { projectId: string };
  const search = useSearch({ strict: false }) as CompareSearch;
  const navigate = useNavigate();
  const { options, baseAlternativeId, isLoading } = useCompareOptions(projectId);
  const go = (a?: string, b?: string, replace = false) =>
    void navigate({ to: "/projects/$projectId/compare", params: { projectId }, search: { a, b }, replace });
  // Wait for every option so the base can be preferred as A.
  const fallback = !isLoading && (!search.a || !search.b) ? defaultPair(options, baseAlternativeId) : null;
  useEffect(() => {
    if (fallback) go(fallback[0], fallback[1], true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fallback?.[0], fallback?.[1]]);
  const find = (id?: string): CompareOption | undefined => options.find((o) => o.resultId === id);
  return {
    projectId,
    options,
    optionsLoading: isLoading,
    a: search.a,
    b: search.b,
    optA: find(search.a),
    optB: find(search.b),
    onPick: (side: "a" | "b", id: string) => (side === "a" ? go(id, search.b) : go(search.a, id)),
    onSwap: () => go(search.b, search.a),
  };
}
