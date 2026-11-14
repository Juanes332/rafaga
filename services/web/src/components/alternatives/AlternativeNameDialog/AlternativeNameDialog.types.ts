import type { Alternative } from "@/types/alternatives/alternative.types";

export interface AlternativeNameDialogProps {
  open: boolean;
  mode: "create" | "rename";
  initialName?: string;
  /** Alternatives that can be copied when creating. */
  sources?: Alternative[];
  pending: boolean;
  error: unknown;
  onOpenChange: (open: boolean) => void;
  onSubmit: (name: string, fromId: string | null) => void;
}
