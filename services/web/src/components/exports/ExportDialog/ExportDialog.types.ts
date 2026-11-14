export type ExportLayer = "k" | "zones" | "speed" | "delta_k" | "lawson";

/** Contract shared by the results view, the comparison and the export dialog (SCR-19). */
export interface ExportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** null → disabled with an explanation (no results in this view). */
  resultId: string | null;
  /** Required for delta_k; makes the export a comparison. */
  compareResultId?: string | null;
  defaultLayer?: ExportLayer;
}
