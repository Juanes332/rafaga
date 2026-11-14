import { useQuery } from "@tanstack/react-query";
import { useShallow } from "zustand/react/shallow";
import { zonesQueryOptions } from "@/api/results/results.queries";
import { settingsQueryOptions } from "@/api/settings/settings.queries";
import type { ZoneLegendItem } from "@/components/results/ZoneLegend/ZoneLegend.types";
import { useResultsStore } from "@/stores/results/results.store";
import type { ResultInspectorProps } from "./ResultInspector.types";

/** Solver warning codes the SPA has copy for; unknown future codes are skipped. */
export const KNOWN_WARNINGS = [
  "element_not_representable_2d",
  "low_reynolds",
  "local_mach_spikes",
  "convergence_cap_reached",
  "domain_top_capped",
  "below_analysis_height",
  "above_building_clamped",
  "element_orphaned",
  "element_degenerate",
  "setback_tiers_truncated",
] as const;

/** Stats, zone areas from /zones with the user's thresholds, and which panel shows. */
export function useResultInspector(p: ResultInspectorProps) {
  const ui = useResultsStore(useShallow((s) => ({ layer: s.layer, zones: s.zones, tool: s.tool })));
  const settings = useQuery(settingsQueryOptions());
  const t = settings.data?.thresholds;
  const isPlan = p.result.kind !== "section2d";
  const zones = useQuery({ ...zonesQueryOptions(p.result.id, t?.k_accel ?? 1.2, t?.k_stagnation ?? 0.3), enabled: isPlan && Boolean(t) });
  const items: ZoneLegendItem[] = (zones.data?.zones ?? [])
    .filter((z) => z.area_m2 > 0)
    .map((z) => ({ zone: z.zone, area_m2: z.area_m2, percent: z.percent }));
  return {
    ...ui,
    isPlan,
    zoneItems: items,
    warnings: [...new Set(p.result.warnings)].filter((w): w is (typeof KNOWN_WARNINGS)[number] => (KNOWN_WARNINGS as readonly string[]).includes(w)),
    zonesError: zones.error,
    showSection: ui.tool === "section" && !p.readOnly,
    showLawson: ui.layer === "lawson" && Boolean(p.result.study_id),
  };
}
