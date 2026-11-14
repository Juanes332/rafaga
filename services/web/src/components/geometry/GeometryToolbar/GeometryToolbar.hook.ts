import { useShallow } from "zustand/react/shallow";
import { useGeometryStore, type EditorTool, type EditorView } from "@/stores/geometry/geometry.store";

export const TOOLS: EditorTool[] = ["select", "rect", "polygon", "ruler"];

/** Toolbar state from the editor store. */
export function useGeometryToolbar() {
  const s = useGeometryStore(
    useShallow((st) => ({
      tool: st.tool,
      view: st.view,
      dirty: st.dirty,
      canUndo: st.past.length > 0,
      canRedo: st.future.length > 0,
      setTool: st.setTool,
      setView: st.setView,
      undo: st.undo,
      redo: st.redo,
    })),
  );
  return {
    ...s,
    onTool: (v: string) => v && s.setTool(v as EditorTool),
    onView: (v: string) => v && s.setView(v as EditorView),
  };
}
