import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
import { projectQueryOptions } from "@/api/projects/projects.queries";
import { terrainCategoriesQueryOptions, useFetchEra5, useUpdateWind, windQueryOptions } from "@/api/wind/wind.queries";
import { useProjectAccess } from "@/hooks/access/use-project-access";
import type { TerrainCategory, WindClimate, WindPatch } from "@/types/wind/wind.types";

export interface UseWindStep {
  projectId: string;
  hasLocation: boolean;
  loading: boolean;
  wind: WindClimate | null;
  terrain: TerrainCategory[];
  elevation: number | null;
  density: number | null;
  readOnly: boolean;
  manual: boolean;
  fetching: boolean;
  fetchError: unknown;
  patchError: unknown;
  onFetch: () => void;
  onManual: () => void;
  onPatch: (patch: WindPatch) => void;
}

/** SCR-10: ERA5 rose, manual wind, terrain roughness. */
export function useWindStep(): UseWindStep {
  const { t } = useTranslation();
  const { projectId } = useParams({ strict: false }) as { projectId: string };
  const project = useQuery(projectQueryOptions(projectId));
  const hasLocation = project.data?.lat != null;
  const wind = useQuery({ ...windQueryOptions(projectId), enabled: hasLocation });
  const terrain = useQuery(terrainCategoriesQueryOptions());
  const era5 = useFetchEra5(projectId);
  const update = useUpdateWind(projectId);
  const [wantsManual, setWantsManual] = useState(false);
  const { readOnly } = useProjectAccess(projectId);
  const data = wind.data ?? null;

  return {
    projectId,
    hasLocation,
    loading: project.isLoading || wind.isLoading,
    wind: data,
    terrain: terrain.data ?? [],
    elevation: project.data?.elevation_m ?? null,
    density: data?.air_density_kg_m3 ?? project.data?.air_density_kg_m3 ?? null,
    readOnly,
    manual: wantsManual || data?.source === "manual",
    fetching: era5.isPending,
    fetchError: era5.error,
    patchError: update.error,
    onFetch: () => era5.mutate(10, { onSuccess: () => (setWantsManual(false), toast(t("wind:fetched"))) }),
    onManual: () => {
      setWantsManual(true);
      if (data?.source !== "manual") update.mutate({ source: "manual", manual_direction_deg: data?.manual_direction_deg ?? 90, manual_u10_ms: data?.manual_u10_ms ?? 5 });
    },
    onPatch: (patch) => update.mutate(patch),
  };
}
