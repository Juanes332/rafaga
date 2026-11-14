import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { toast } from "sonner";
import { useTranslation } from "react-i18next";
import { useSetLocation } from "@/api/location/location.queries";
import { projectQueryOptions, useUpdateProject } from "@/api/projects/projects.queries";
import { useProjectAccess } from "@/hooks/access/use-project-access";
import { hasCode } from "@/lib/http/api-error";
import type { Project } from "@/types/projects/project.types";

export interface UseLocationStep {
  projectId: string;
  project: Project | undefined;
  hasLocation: boolean;
  readOnly: boolean;
  pending: boolean;
  needsElevation: boolean;
  error: unknown;
  onPick: (lat: number, lon: number) => void;
  onManualElevation: (elevation: number) => void;
  onHeight: (h: number) => void;
}

/** SCR-05: one mutation fed by map click, place search or typed coordinates. */
export function useLocationStep(): UseLocationStep {
  const { t } = useTranslation();
  const { projectId } = useParams({ strict: false }) as { projectId: string };
  const project = useQuery(projectQueryOptions(projectId));
  const setLocation = useSetLocation(projectId);
  const update = useUpdateProject();
  const { readOnly } = useProjectAccess(projectId);
  const [pick, setPick] = useState<{ lat: number; lon: number } | null>(null);
  const needsElevation = hasCode(setLocation.error, "elevation_unavailable");
  const saved = () => toast(t("location:saved"));

  return {
    projectId,
    project: project.data,
    hasLocation: project.data?.lat != null,
    readOnly,
    pending: setLocation.isPending,
    needsElevation,
    error: needsElevation ? null : (setLocation.error ?? update.error),
    onPick: (lat, lon) => {
      if (readOnly) return;
      setPick({ lat, lon });
      setLocation.mutate({ lat, lon }, { onSuccess: saved });
    },
    onManualElevation: (elevation) =>
      pick && setLocation.mutate({ ...pick, elevation_m: elevation }, { onSuccess: saved }),
    onHeight: (h) => update.mutate({ id: projectId, patch: { analysis_height_m: h } }),
  };
}
