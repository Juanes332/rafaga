import { useQuery } from "@tanstack/react-query";
import { useRouterState } from "@tanstack/react-router";
import { projectQueryOptions } from "@/api/projects/projects.queries";
import { geometryQueryOptions } from "@/api/geometry/geometry.queries";
import { windQueryOptions } from "@/api/wind/wind.queries";
import { alternativesQueryOptions } from "@/api/alternatives/alternatives.queries";
import { studiesQueryOptions } from "@/api/simulations/simulations.queries";
import type { StepItem } from "./StepRail.types";
import { computeSteps, stepFromPath } from "./StepRail.utils";

/** Step states from the project's server data and the current route. */
export function useStepRail(projectId: string): StepItem[] {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const project = useQuery(projectQueryOptions(projectId));
  const hasLocation = project.data?.lat != null;
  const geometry = useQuery(geometryQueryOptions(projectId));
  const wind = useQuery({ ...windQueryOptions(projectId), enabled: hasLocation });
  const alternatives = useQuery(alternativesQueryOptions(projectId));
  const studies = useQuery(studiesQueryOptions(projectId));
  return computeSteps({
    hasLocation,
    buildingCount: geometry.data?.buildings.length ?? 0,
    hasWind: wind.data != null,
    alternativeCount: alternatives.data?.length ?? 0,
    completedStudies: (studies.data ?? []).filter((s) => s.status === "completed" || s.status === "partial").length,
    current: stepFromPath(pathname),
  });
}
