import type { GridView } from "@/engines/fields/grid-view";
import type { Blob } from "@/engines/fields/zones";
import type { ZoneKind } from "@/engines/fields/zone-patterns";
import type { Building } from "@/types/geometry/geometry.types";
import type { OutputGridPlan } from "@/types/simulations/simulation.types";

export interface ZoneLabel {
  zone: ZoneKind;
  blob: Blob;
}

export interface PlanOverlayProps {
  view: GridView;
  grid: OutputGridPlan;
  buildings: Building[];
  labels: ZoneLabel[];
  /** Section line in ENU metres (0, 1 or 2 points). */
  section: Array<[number, number]>;
}
