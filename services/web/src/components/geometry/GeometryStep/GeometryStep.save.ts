import { useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { geometryQueryOptions, useSaveGeometry, useValidateGeometry } from "@/api/geometry/geometry.queries";
import { useQueryClient } from "@tanstack/react-query";
import { hasCode } from "@/lib/http/api-error";
import { useGeometryStore } from "@/stores/geometry/geometry.store";
import type { GeometryIssue } from "@/types/geometry/geometry.types";

/** Save with optimistic concurrency; base_locked asks first, version_conflict offers a reload. */
export function useGeometrySave(projectId: string) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const save = useSaveGeometry(projectId);
  const validate = useValidateGeometry(projectId);
  const [confirming, setConfirming] = useState(false);
  const [serverIssues, setServerIssues] = useState<GeometryIssue[]>([]);

  const run = (confirmBaseChange = false) => {
    const s = useGeometryStore.getState();
    save.mutate(
      { expectedVersion: s.baseVersion, buildings: s.buildings, confirmBaseChange },
      {
        onSuccess: (g) => {
          useGeometryStore.getState().markSaved(g.version);
          setServerIssues(g.issues);
          setConfirming(false);
          const orphaned = g.orphaned_elements?.length ?? 0;
          toast(orphaned ? t("geometry:orphaned", { count: orphaned }) : t("geometry:tools.saved"));
        },
        onError: (e) => hasCode(e, "base_locked") && setConfirming(true),
      },
    );
  };

  const reload = async () => {
    const fresh = await qc.fetchQuery({ ...geometryQueryOptions(projectId), staleTime: 0 });
    useGeometryStore.getState().load(projectId, fresh);
    save.reset();
  };

  const check = () =>
    validate.mutate(useGeometryStore.getState().buildings, { onSuccess: (r) => setServerIssues(r.issues) });

  return {
    save: () => run(false),
    confirmSave: () => run(true),
    confirming,
    cancelConfirm: () => (setConfirming(false), save.reset()),
    saving: save.isPending,
    error: hasCode(save.error, "base_locked") ? null : save.error,
    conflict: hasCode(save.error, "version_conflict"),
    reload,
    check,
    checking: validate.isPending,
    serverIssues,
  };
}
