import type { ComparisonAreas, ComparisonComfort } from "@/types/comparisons/comparison.types";

export interface CompareTableProps {
  labelA: string;
  labelB: string;
  areas: ComparisonAreas | undefined;
  comfort: ComparisonComfort | undefined;
  comfortMissing: boolean;
}
