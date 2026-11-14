import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { alternativesQueryOptions } from "@/api/alternatives/alternatives.queries";
import { projectQueryOptions } from "@/api/projects/projects.queries";
import { windQueryOptions } from "@/api/wind/wind.queries";
import { useProjectAccess } from "@/hooks/access/use-project-access";
import { useSimulationFormStore } from "@/stores/simulations/simulations.store";
import type { Alternative } from "@/types/alternatives/alternative.types";
import type { WindSector } from "@/types/wind/wind.types";

export interface UseSimulateStep {
  projectId: string;
  loading: boolean;
  hasLocation: boolean;
  sectors: WindSector[] | null;
  alternatives: Alternative[];
  readOnly: boolean;
}

/** SCR-12/13 context: location gate, rose for coverage, alternatives to simulate. */
export function useSimulateStep(): UseSimulateStep {
  const { projectId } = useParams({ strict: false }) as { projectId: string };
  const project = useQuery(projectQueryOptions(projectId));
  const hasLocation = project.data?.lat != null;
  const wind = useQuery({ ...windQueryOptions(projectId), enabled: hasLocation });
  const alternatives = useQuery(alternativesQueryOptions(projectId));
  const { readOnly } = useProjectAccess(projectId);
  const forProject = useSimulationFormStore((s) => s.forProject);
  useEffect(() => {
    forProject(projectId);
  }, [forProject, projectId]);
  return {
    projectId,
    loading: project.isLoading,
    hasLocation,
    sectors: wind.data?.rose?.sectors ?? null,
    alternatives: alternatives.data ?? [],
    readOnly,
  };
}
