import { useCallback, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { templatesQueryOptions, useDeleteTemplate } from "@/api/templates/templates.queries";
import { errorMessage } from "@/lib/http/error-copy";
import type { Template } from "@/types/settings/settings.types";

/** SCR-23: list, delete, and the template chosen for applying. */
export function useTemplatesScreen() {
  const { t } = useTranslation();
  const list = useQuery(templatesQueryOptions());
  const remove = useDeleteTemplate();
  const [applying, setApplying] = useState<Template | null>(null);
  const onDelete = useCallback(
    (tpl: Template) =>
      remove.mutate(tpl.id, {
        onSuccess: () => toast(t("templates:delete.done")),
        onError: (e) => toast.error(errorMessage(e)),
      }),
    [remove, t],
  );
  return {
    templates: list.data ?? [],
    empty: list.isSuccess && (list.data ?? []).length === 0,
    error: list.error,
    applying,
    onApply: useCallback((tpl: Template) => setApplying(tpl), []),
    onCloseApply: () => setApplying(null),
    onDelete,
  };
}
