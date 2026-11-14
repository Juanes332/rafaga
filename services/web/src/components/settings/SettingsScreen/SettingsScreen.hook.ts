import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { settingsQueryOptions, useUpdateSettings } from "@/api/settings/settings.queries";
import type { Settings } from "@/types/settings/settings.types";
import { orderErrors, serverFieldErrors, toPatch, withPath, type Path } from "./SettingsScreen.utils";

export interface SettingsDraft {
  draft: Settings;
  set: (path: Path, value: number) => void;
  fieldErrors: string[];
  order: { zones: boolean; lawson: boolean };
}

/** Draft copy of the settings; saved as one PATCH so zones re-threshold once. */
export function useSettingsScreen() {
  const { t } = useTranslation();
  const query = useQuery(settingsQueryOptions());
  const update = useUpdateSettings();
  const [draft, setDraft] = useState<Settings | null>(null);
  useEffect(() => {
    if (query.data && draft === null) setDraft(query.data);
  }, [query.data, draft]);

  const order = draft ? orderErrors(draft) : { zones: false, lawson: false };
  const dirty = draft !== null && JSON.stringify(draft) !== JSON.stringify(query.data);
  const onSave = () =>
    draft &&
    update.mutate(toPatch(draft), {
      onSuccess: (s) => (setDraft(s), toast(t("settings:saved"))),
    });

  return {
    loading: query.isLoading,
    loadError: query.error,
    form: draft
      ? ({
          draft,
          set: (path: Path, value: number) => setDraft((d) => (d ? withPath(d, path, value) : d)),
          fieldErrors: serverFieldErrors(update.error),
          order,
        } satisfies SettingsDraft)
      : null,
    saveError: serverFieldErrors(update.error).length > 0 ? null : update.error,
    canSave: dirty && !order.zones && !order.lawson && !update.isPending,
    saving: update.isPending,
    dirty,
    onSave,
    onReset: () => setDraft(query.data ?? null),
  };
}
