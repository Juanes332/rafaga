import type { Field } from "@/engines/fields/field.decode";
import type { Building } from "@/types/geometry/geometry.types";
import type { Thresholds } from "@/types/settings/settings.types";
import type { OutputGridPlan } from "@/types/simulations/simulation.types";

export interface CompareStageProps {
  a: Field;
  b: Field;
  grid: OutputGridPlan;
  buildings: Building[];
  thresholds: Thresholds;
  labelA: string;
  labelB: string;
}
