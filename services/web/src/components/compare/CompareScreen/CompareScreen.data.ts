import { useQuery } from "@tanstack/react-query";
import { comparisonAreasQueryOptions, comparisonCheckQueryOptions, comparisonComfortQueryOptions } from "@/api/comparisons/comparisons.queries";
import { geometryQueryOptions } from "@/api/geometry/geometry.queries";
import { fieldQueryOptions, resultQueryOptions } from "@/api/results/results.queries";
import { settingsQueryOptions } from "@/api/settings/settings.queries";
import type { OutputGridPlan } from "@/types/simulations/simulation.types";

const DEFAULT_T = { k_accel: 1.2, k_stagnation: 0.3, dk_reduction: -0.1 };

/** Comparability check, both K fields, areas and comfort for the selected pair. */
export function useCompareData(projectId: string, a = "", b = "") {
  const pair = Boolean(a && b);
  const check = useQuery({ ...comparisonCheckQueryOptions(a, b), enabled: pair });
  const ok = check.data?.comparable === true;
  const ra = useQuery({ ...resultQueryOptions(a), enabled: pair });
  const rb = useQuery({ ...resultQueryOptions(b), enabled: pair });
  const ka = useQuery({ ...fieldQueryOptions(a, "K"), enabled: ok });
  const kb = useQuery({ ...fieldQueryOptions(b, "K"), enabled: ok });
  const settings = useQuery(settingsQueryOptions());
  const thresholds = settings.data?.thresholds ?? DEFAULT_T;
  const areas = useQuery({ ...comparisonAreasQueryOptions(a, b, thresholds), enabled: ok });
  const sa = ra.data?.study_id ?? "";
  const sb = rb.data?.study_id ?? "";
  const comfort = useQuery({ ...comparisonComfortQueryOptions(sa, sb), enabled: ok && Boolean(sa && sb), retry: false });
  const geometry = useQuery(geometryQueryOptions(projectId));
  return {
    pair,
    check: check.data,
    error: check.error ?? ka.error ?? kb.error,
    loading: pair && (check.isLoading || (ok && (ka.isLoading || kb.isLoading))),
    ka: ka.data,
    kb: kb.data,
    grid: ra.data?.output_grid as OutputGridPlan | undefined,
    thresholds,
    areas: areas.data,
    comfort: comfort.data,
    comfortMissing: comfort.isError,
    buildings: geometry.data?.buildings ?? [],
  };
}
