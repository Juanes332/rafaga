import { useNavigate } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { useShallow } from "zustand/react/shallow";
import { useLaunchSection } from "@/api/simulations/sections.queries";
import { useResultsStore } from "@/stores/results/results.store";
import type { SectionPanelProps } from "./SectionPanel.types";
import { runsDownwind, sectionLength } from "./SectionPanel.utils";

/** SCR-17: two clicked points → section2d study, then follow it in Simular. */
export function useSectionPanel(p: SectionPanelProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { section, setTool } = useResultsStore(useShallow((s) => ({ section: s.section, setTool: s.setTool })));
  const mutation = useLaunchSection();
  const complete = section.length === 2;
  const against = complete && !runsDownwind(section[0], section[1], p.directionDeg);
  const launch = () => {
    if (!complete || !p.alternativeId) return;
    mutation.mutate(
      { projectId: p.projectId, alternativeId: p.alternativeId, section: { p0: section[0], p1: section[1] }, dxM: p.dxM },
      {
        onSuccess: () => {
          toast(t("results:section.launched"));
          setTool("none");
          void navigate({ to: "/projects/$projectId/simulate", params: { projectId: p.projectId } });
        },
      },
    );
  };
  return {
    section,
    complete,
    against,
    length: complete ? sectionLength(section[0], section[1]) : null,
    canLaunch: complete && !against && Boolean(p.alternativeId) && !mutation.isPending,
    pending: mutation.isPending,
    error: mutation.error,
    launch,
    clear: () => setTool("section"),
  };
}
