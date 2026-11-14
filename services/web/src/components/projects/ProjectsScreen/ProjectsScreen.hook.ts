import { useCallback, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import {
  projectsQueryOptions,
  useCreateProject,
  useDeleteProject,
  useDuplicateProject,
  useUpdateProject,
} from "@/api/projects/projects.queries";
import { errorMessage } from "@/lib/http/error-copy";
import type { ProjectSummary } from "@/types/projects/project.types";

function useCreateFlow() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const create = useCreateProject();
  const [creating, setOpen] = useState(false);
  const onCreate = (name: string) =>
    create.mutate(name, {
      onSuccess: (p) => {
        toast(t("projects:toast.created"));
        void navigate({ to: "/projects/$projectId/location", params: { projectId: p.id } });
      },
    });
  return { creating, setCreating: (o: boolean) => (create.reset(), setOpen(o)), create, onCreate };
}

function useRenameFlow() {
  const { t } = useTranslation();
  const update = useUpdateProject();
  const [renaming, setRenaming] = useState<ProjectSummary | null>(null);
  const onRenameSubmit = (name: string) =>
    renaming &&
    update.mutate(
      { id: renaming.id, patch: { name } },
      { onSuccess: () => (setRenaming(null), toast(t("projects:toast.renamed"))) },
    );
  return { renaming, setRenaming, update, onRenameSubmit };
}

function useDuplicateFlow() {
  const { t } = useTranslation();
  const duplicate = useDuplicateProject();
  const onDuplicate = useCallback(
    (p: ProjectSummary) =>
      duplicate.mutate(p.id, {
        onSuccess: () => toast(t("projects:toast.duplicated")),
        onError: (e) => toast.error(errorMessage(e)),
      }),
    [duplicate, t],
  );
  return { onDuplicate };
}

function useDeleteFlow() {
  const { t } = useTranslation();
  const remove = useDeleteProject();
  const [deleting, setDeleting] = useState<ProjectSummary | null>(null);
  const onConfirmDelete = () =>
    deleting &&
    remove.mutate(deleting.id, {
      onSuccess: () => (setDeleting(null), toast(t("projects:toast.deleted"))),
      onError: (e) => toast.error(errorMessage(e)),
    });
  return { deleting, setDeleting, onConfirmDelete };
}

/** SCR-03 orchestration: list query plus the create, rename, duplicate and delete flows. */
export function useProjectsScreen() {
  const list = useQuery(projectsQueryOptions());
  return {
    projects: list.data ?? [],
    isLoading: list.isLoading,
    error: list.error,
    retry: () => void list.refetch(),
    ...useCreateFlow(),
    ...useRenameFlow(),
    ...useDuplicateFlow(),
    ...useDeleteFlow(),
  };
}
