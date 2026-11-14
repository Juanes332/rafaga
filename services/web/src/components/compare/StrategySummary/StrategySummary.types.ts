import type { Field } from "@/engines/fields/field.decode";
import type { ComparisonAreas, ComparisonComfort } from "@/types/comparisons/comparison.types";

export interface StrategySummaryProps {
  nameA: string;
  nameB: string;
  ka: Field;
  kb: Field;
  areas: ComparisonAreas | undefined;
  comfort: ComparisonComfort | undefined;
  comfortMissing: boolean;
  dkReduction: number;
}
