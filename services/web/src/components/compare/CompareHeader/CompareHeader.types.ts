import type { CompareOption } from "@/components/compare/CompareScreen/CompareScreen.options";

export interface CompareHeaderProps {
  projectId: string;
  options: CompareOption[];
  a: string | undefined;
  b: string | undefined;
  direction: string | null;
  deltaK: boolean;
  zones: boolean;
  canExport: boolean;
  onPick: (side: "a" | "b", resultId: string) => void;
  onSwap: () => void;
  onToggleDeltaK: () => void;
  onToggleZones: () => void;
  onExport: () => void;
}
