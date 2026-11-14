import type { Result } from "@/types/results/result.types";

export interface ResultInspectorProps {
  projectId: string;
  result: Result;
  alternativeName: string;
  alternativeId: string | null;
  readOnly: boolean;
  onExport: () => void;
}
