import { useShallow } from "zustand/react/shallow";
import { useResultsStore, type ResultLayer } from "@/stores/results/results.store";

/** Toolbar state: layer, zones, section tool, 3D toggle. */
export function useResultsToolbar() {
  const s = useResultsStore(
    useShallow((st) => ({
      layer: st.layer,
      zones: st.zones,
      tool: st.tool,
      view3d: st.view3d,
      setLayer: st.setLayer,
      toggleZones: st.toggleZones,
      setTool: st.setTool,
      setView3d: st.setView3d,
    })),
  );
  return {
    ...s,
    onLayer: (v: string) => v && s.setLayer(v as ResultLayer),
    toggleSection: () => s.setTool(s.tool === "section" ? "none" : "section"),
    toggle3d: () => s.setView3d(!s.view3d),
  };
}
