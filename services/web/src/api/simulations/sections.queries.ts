import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import type { SectionLine, Study } from "@/types/simulations/simulation.types";

export interface SectionLaunch {
  projectId: string;
  alternativeId: string;
  section: SectionLine;
  dxM: number;
}

/** SCR-17: launch a section2d study along a line drawn upwind → downwind. */
export function useLaunchSection() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (p: SectionLaunch) =>
      apiClient.post<Study>("/simulations", {
        alternative_id: p.alternativeId,
        kind: "section2d",
        section: p.section,
        dx_m: p.dxM,
        device: "auto",
      }),
    onSuccess: (_s, p) => qc.invalidateQueries({ queryKey: ["simulations", p.projectId] }),
  });
}
