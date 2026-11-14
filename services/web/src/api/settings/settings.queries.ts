import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import type { Settings, SettingsPatch } from "@/types/settings/settings.types";

export const settingsKeys = { detail: ["settings"] as const };

/** Per-user thresholds, Lawson table and defaults (SCR-21); zones re-threshold from these. */
export const settingsQueryOptions = () =>
  queryOptions({ queryKey: settingsKeys.detail, queryFn: () => apiClient.get<Settings>("/settings") });

/** PATCH /settings; the new values flow to every zone/legend through the settings query. */
export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (patch: SettingsPatch) => apiClient.patch<Settings>("/settings", patch),
    onSuccess: (s) => {
      qc.setQueryData(settingsKeys.detail, s);
      // Zone areas and comfort are keyed by thresholds; refetch whatever is on screen.
      return Promise.all([
        qc.invalidateQueries({ queryKey: ["results"] }),
        qc.invalidateQueries({ queryKey: ["comparisons"] }),
      ]);
    },
  });
}
