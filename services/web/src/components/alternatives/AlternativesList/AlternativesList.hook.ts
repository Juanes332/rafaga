import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { useCreateAlternative, useDeleteAlternative, useUpdateAlternative } from "@/api/alternatives/alternatives.queries";
import { errorMessage } from "@/lib/http/error-copy";
import type { Alternative } from "@/types/alternatives/alternative.types";
import type { AlternativesListProps } from "./AlternativesList.types";

/** Create / rename / delete dialogs and their mutations. */
export function useAlternativesList(p: AlternativesListProps) {
  const { t } = useTranslation();
  const create = useCreateAlternative(p.projectId);
  const update = useUpdateAlternative(p.projectId);
  const remove = useDeleteAlternative(p.projectId);
  const [creating, setCreating] = useState(false);
  const [renaming, setRenaming] = useState<Alternative | null>(null);
  const [deleting, setDeleting] = useState<Alternative | null>(null);

  const onCreate = (name: string, fromId: string | null) =>
    create.mutate(
      { name, ...(fromId ? { from_alternative_id: fromId } : {}) },
      { onSuccess: (alt) => (setCreating(false), p.onSelect(alt.id), toast(t("alternatives:toast.created"))) },
    );
  const onRename = (name: string) =>
    renaming && update.mutate({ id: renaming.id, patch: { name } }, { onSuccess: () => (setRenaming(null), toast(t("alternatives:toast.renamed"))) });
  const onDelete = () =>
    deleting &&
    remove.mutate(deleting.id, {
      onSuccess: () => (setDeleting(null), toast(t("alternatives:toast.deleted"))),
      onError: (e) => (setDeleting(null), toast.error(errorMessage(e))),
    });

  return {
    creating,
    openCreate: (o: boolean) => (create.reset(), setCreating(o)),
    create,
    onCreate,
    renaming,
    setRenaming,
    update,
    onRename,
    deleting,
    setDeleting,
    onDelete,
  };
}
