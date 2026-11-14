import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate, useParams } from "@tanstack/react-router";
import { resultQueryOptions } from "@/api/results/results.queries";
import { studyQueryOptions } from "@/api/simulations/simulations.queries";
import type { DirectionOption } from "@/components/results/ResultsToolbar/ResultsToolbar.types";
import { useProjectAccess } from "@/hooks/access/use-project-access";
import { directionLabel } from "@/lib/format/format.direction";
import { useResultsStore } from "@/stores/results/results.store";

/** Result + its study (directions, alternative), access and export dialog state. */
export function useResultsStep() {
  const { projectId, resultId } = useParams({ strict: false }) as { projectId: string; resultId: string };
  const navigate = useNavigate();
  const result = useQuery(resultQueryOptions(resultId));
  const studyId = result.data?.study_id ?? "";
  const study = useQuery({ ...studyQueryOptions(studyId), enabled: Boolean(studyId) });
  const { readOnly } = useProjectAccess(projectId);
  const view3d = useResultsStore((s) => s.view3d);
  const setTool = useResultsStore((s) => s.setTool);
  const setView3d = useResultsStore((s) => s.setView3d);
  const [exportOpen, setExportOpen] = useState(false);
  useEffect(() => {
    setTool("none");
    setView3d(false);
  }, [resultId, setTool, setView3d]);

  const directions: DirectionOption[] = (study.data?.jobs ?? [])
    .filter((j) => j.result_id && j.status === "completed" && j.direction_deg != null)
    .map((j) => ({ resultId: j.result_id as string, label: directionLabel(j.direction_deg as number) }));
  return {
    projectId,
    resultId,
    result: result.data,
    error: result.error,
    isLoading: result.isLoading,
    alternativeName: study.data?.alternative_name ?? "",
    alternativeId: study.data?.alternative_id ?? null,
    directions,
    readOnly,
    view3d,
    exportOpen,
    setExportOpen,
    onDirection: (id: string) => void navigate({ to: "/projects/$projectId/results/$resultId", params: { projectId, resultId: id } }),
  };
}
