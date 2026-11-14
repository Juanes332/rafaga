import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { geometryQueryOptions } from "@/api/geometry/geometry.queries";
import { useGeometryStore } from "@/stores/geometry/geometry.store";

/** Loads server geometry into the draft on project change, or when a newer version arrives and nothing is unsaved. */
export function useGeometrySync(projectId: string) {
  const query = useQuery(geometryQueryOptions(projectId));
  const { data } = query;
  useEffect(() => {
    if (!data) return;
    const s = useGeometryStore.getState();
    if (s.projectId !== projectId || (!s.dirty && data.version !== s.baseVersion)) s.load(projectId, data);
  }, [data, projectId]);
  return query;
}

/** Ctrl/Cmd+Z undo, Ctrl/Cmd+Shift+Z or Ctrl+Y redo; ignored while typing in a field. */
export function useUndoShortcuts(enabled: boolean): void {
  useEffect(() => {
    if (!enabled) return;
    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (target?.closest("input, textarea, select, [contenteditable=true]")) return;
      if (!(e.ctrlKey || e.metaKey)) return;
      const key = e.key.toLowerCase();
      const s = useGeometryStore.getState();
      if (key === "z" && !e.shiftKey) s.undo();
      else if ((key === "z" && e.shiftKey) || key === "y") s.redo();
      else return;
      e.preventDefault();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [enabled]);
}
