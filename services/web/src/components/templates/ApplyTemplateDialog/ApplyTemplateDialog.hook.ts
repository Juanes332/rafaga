import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { projectsQueryOptions } from "@/api/projects/projects.queries";
import { useApplyTemplate } from "@/api/templates/templates.queries";
import type { Template } from "@/types/settings/settings.types";

/** Project picker for applying one template; only projects you own can change. */
export function useApplyTemplateDialog(template: Template | null, onDone: () => void) {
  const { t } = useTranslation();
  const [projectId, setProjectId] = useState("");
  const projects = useQuery(projectsQueryOptions());
  const apply = useApplyTemplate();
  useEffect(() => {
    if (template) {
      setProjectId("");
      apply.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [template]);
  const owned = (projects.data ?? []).filter((p) => p.role_on_project === "owner");

  const onApply = () => {
    if (!template || !projectId) return;
    const project = owned.find((p) => p.id === projectId)?.name ?? "";
    apply.mutate(
      { projectId, templateId: template.id },
      { onSuccess: () => (toast(t("templates:apply.done", { project })), onDone()) },
    );
  };
  return { projectId, setProjectId, projects: owned, error: apply.error, pending: apply.isPending, onApply };
}
