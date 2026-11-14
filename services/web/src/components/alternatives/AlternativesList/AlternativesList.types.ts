import type { Alternative } from "@/types/alternatives/alternative.types";

export interface AlternativesListProps {
  projectId: string;
  alternatives: Alternative[];
  selectedId: string | null;
  readOnly: boolean;
  onSelect: (id: string) => void;
}
