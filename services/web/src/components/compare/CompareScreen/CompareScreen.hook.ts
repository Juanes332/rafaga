import { useEffect, useState } from "react";
import { useShallow } from "zustand/react/shallow";
import { useProjectAccess } from "@/hooks/access/use-project-access";
import { directionLabel } from "@/lib/format/format.direction";
import { useCompareStore } from "@/stores/compare/compare.store";
import { useCompareData } from "./CompareScreen.data";
import { useComparePair } from "./CompareScreen.pair";

/** SCR-18 orchestration: pair in the URL, data, toggles, export. */
export function useCompareScreen() {
  const pair = useComparePair();
  const data = useCompareData(pair.projectId, pair.a, pair.b);
  const { readOnly } = useProjectAccess(pair.projectId);
  const ui = useCompareStore(useShallow((s) => ({ deltaK: s.deltaK, zones: s.zones, toggleDeltaK: s.toggleDeltaK, toggleZones: s.toggleZones, reset: s.reset })));
  const [exportOpen, setExportOpen] = useState(false);
  const { reset } = ui;
  useEffect(() => reset, [reset]);
  const empty = !pair.optionsLoading && pair.options.length < 2 && !(pair.a && pair.b);
  return {
    ...pair,
    ...data,
    ...ui,
    empty,
    readOnly,
    labelA: pair.optA?.label ?? "",
    labelB: pair.optB?.label ?? "",
    nameA: pair.optA?.name ?? "",
    nameB: pair.optB?.name ?? "",
    direction: pair.optA ? directionLabel(pair.optA.direction) : null,
    exportOpen,
    setExportOpen,
  };
}
