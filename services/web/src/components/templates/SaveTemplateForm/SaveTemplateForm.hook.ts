import { useState, type FormEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { facadeStrategiesQueryOptions } from "@/api/facades/facades.queries";
import { projectsQueryOptions } from "@/api/projects/projects.queries";
import { settingsQueryOptions } from "@/api/settings/settings.queries";
import { useCreateTemplate } from "@/api/templates/templates.queries";
import { windQueryOptions } from "@/api/wind/wind.queries";
import { buildPayload } from "./SaveTemplateForm.utils";

/** Name + source project; the payload is assembled from settings, wind and strategy defaults. */
export function useSaveTemplateForm() {
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [projectId, setProjectId] = useState("");
  const [nameError, setNameError] = useState<string | null>(null);
  const projects = useQuery(projectsQueryOptions());
  const settings = useQuery(settingsQueryOptions());
  const strategies = useQuery(facadeStrategiesQueryOptions());
  const wind = useQuery({ ...windQueryOptions(projectId), enabled: projectId !== "" });
  const create = useCreateTemplate();

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return setNameError(t("templates:create.nameRequired"));
    if (!settings.data) return;
    setNameError(null);
    const payload = buildPayload(settings.data, wind.data, strategies.data ?? []);
    create.mutate(
      { name: name.trim(), payload },
      { onSuccess: () => (setName(""), toast(t("templates:create.saved"))) },
    );
  };
  return {
    name,
    setName,
    projectId,
    setProjectId,
    projects: projects.data ?? [],
    noWind: projectId !== "" && wind.isFetched && wind.data == null,
    nameError,
    error: create.error,
    pending: create.isPending || !settings.data,
    onSubmit,
  };
}
