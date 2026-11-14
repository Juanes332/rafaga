import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import type { Estimate, EstimateRequest, Job, SimulationCreate, Study, StudySummary } from "@/types/simulations/simulation.types";

export const simulationsKeys = {
  list: (projectId: string) => ["simulations", projectId] as const,
  detail: (studyId: string) => ["simulations", "study", studyId] as const,
  estimate: (req: EstimateRequest) => ["simulations", "estimate", req] as const,
};

const ACTIVE = new Set(["queued", "running"]);

/** True while any job of the study can still change (ADR-07 polling condition). */
export function isStudyActive(study: Pick<Study, "status" | "jobs"> | undefined): boolean {
  if (!study) return false;
  return ACTIVE.has(study.status) || study.jobs.some((j) => ACTIVE.has(j.status));
}

/** Study list; polled every 3 s while the jobs screen is visible (ADR-07). */
export const studiesQueryOptions = (projectId: string, poll = false) =>
  queryOptions({
    queryKey: simulationsKeys.list(projectId),
    queryFn: () => apiClient.get<StudySummary[]>(`/projects/${projectId}/simulations`),
    refetchInterval: poll ? 3_000 : false,
  });

/** One study; polled every 1 s while any job is queued or running (ADR-07). */
export const studyQueryOptions = (studyId: string) =>
  queryOptions({
    queryKey: simulationsKeys.detail(studyId),
    queryFn: () => apiClient.get<Study>(`/simulations/${studyId}`),
    refetchInterval: (q) => (isStudyActive(q.state.data) ? 1_000 : false),
  });

/** POST /simulations/estimate as a query: nodes, memory vs budget, ETA, proposed dx. */
export const estimateQueryOptions = (req: EstimateRequest, enabled: boolean) =>
  queryOptions({
    queryKey: simulationsKeys.estimate(req),
    queryFn: () => apiClient.post<Estimate>("/simulations/estimate", req),
    enabled,
    staleTime: 30_000,
  });

function useRefreshStudies(projectId: string) {
  const qc = useQueryClient();
  return (study?: Study) => {
    if (study) qc.setQueryData(simulationsKeys.detail(study.id), study);
    return qc.invalidateQueries({ queryKey: simulationsKeys.list(projectId) });
  };
}

/** POST /simulations → 202 Study with one job per direction. */
export function useCreateSimulation(projectId: string) {
  const refresh = useRefreshStudies(projectId);
  return useMutation({
    mutationFn: (body: SimulationCreate) => apiClient.post<Study>("/simulations", body),
    onSuccess: (s) => refresh(s),
  });
}

export function useCancelStudy(projectId: string) {
  const refresh = useRefreshStudies(projectId);
  return useMutation({
    mutationFn: (studyId: string) => apiClient.post<Study>(`/simulations/${studyId}/cancel`),
    onSuccess: (s) => refresh(s),
  });
}

function useJobAction(projectId: string, action: "cancel" | "retry") {
  const qc = useQueryClient();
  const refresh = useRefreshStudies(projectId);
  return useMutation({
    mutationFn: (jobId: string) => apiClient.post<Job>(`/jobs/${jobId}/${action}`),
    onSuccess: (job) => {
      if (job.study_id) void qc.invalidateQueries({ queryKey: simulationsKeys.detail(job.study_id) });
      return refresh();
    },
  });
}

export const useCancelJob = (projectId: string) => useJobAction(projectId, "cancel");
export const useRetryJob = (projectId: string) => useJobAction(projectId, "retry");
