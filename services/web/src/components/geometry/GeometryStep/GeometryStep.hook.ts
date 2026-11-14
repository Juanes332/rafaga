import { useState } from "react";
import { useParams } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { useProjectAccess } from "@/hooks/access/use-project-access";
import { useMediaQuery } from "@/hooks/media/use-media-query";
import { useGeometryStore } from "@/stores/geometry/geometry.store";
import { useGeometrySave } from "./GeometryStep.save";
import { useGeometrySync, useUndoShortcuts } from "./GeometryStep.sync";

/** SCR-06 orchestration: sync draft ↔ server, dialogs, save flow and shortcuts. */
export function useGeometryStep() {
  const { t } = useTranslation();
  const { projectId } = useParams({ strict: false }) as { projectId: string };
  const { readOnly } = useProjectAccess(projectId);
  const query = useGeometrySync(projectId);
  const save = useGeometrySave(projectId);
  useUndoShortcuts(!readOnly);
  const [importOpen, setImportOpen] = useState(false);
  const [traceOpen, setTraceOpen] = useState(false);
  const loaded = useGeometryStore((s) => s.projectId === projectId);
  const count = useGeometryStore((s) => s.buildings.length);
  const tool = useGeometryStore((s) => s.tool);
  const view = useGeometryStore((s) => s.view);
  const hasSelection = useGeometryStore((s) => s.selectedId !== null);
  const small = useMediaQuery("(max-width: 767px)");
  return {
    projectId,
    readOnly,
    loading: query.isLoading || (!loaded && !query.error),
    loadError: query.error,
    retry: () => void query.refetch(),
    empty: loaded && count === 0,
    view,
    hasSelection,
    hint: t(`geometry:hints.${tool}`),
    small,
    save,
    importOpen,
    setImportOpen,
    traceOpen,
    setTraceOpen,
    startDrawing: () => useGeometryStore.getState().setTool("rect"),
  };
}
