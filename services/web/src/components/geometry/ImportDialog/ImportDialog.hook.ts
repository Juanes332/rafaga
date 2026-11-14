import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { useImportGeometry, type ImportUnit } from "@/api/geometry/geometry.queries";
import { updateBuilding } from "@/engines/geometry/buildings";
import { useGeometryStore } from "@/stores/geometry/geometry.store";
import type { ImportReport } from "@/types/geometry/geometry.types";
import type { ImportDialogProps } from "./ImportDialog.types";
import { IMPORT_MAX_BYTES, formatMegabytes, importErrorText } from "./ImportDialog.utils";

/** Upload → report → optional heights; the import is one undoable step in the draft. */
export function useImportDialog({ projectId, onOpenChange }: ImportDialogProps) {
  const { t } = useTranslation();
  const mutation = useImportGeometry(projectId);
  const [file, setFile] = useState<File | null>(null);
  const [unit, setUnit] = useState<ImportUnit>("auto");
  const [mode, setMode] = useState<"append" | "replace">("append");
  const [sizeError, setSizeError] = useState<string | null>(null);
  const [report, setReport] = useState<ImportReport | null>(null);

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!file) return;
    if (file.size > IMPORT_MAX_BYTES) return setSizeError(t("geometry:import.tooLarge", { size: formatMegabytes(file.size) }));
    setSizeError(null);
    mutation.mutate(
      { file, unit, mode },
      {
        onSuccess: (r) => {
          const s = useGeometryStore.getState();
          if (r.geometry) {
            s.apply(r.geometry.buildings);
            s.markSaved(r.geometry.version);
          }
          setReport(r);
        },
      },
    );
  };

  const applyHeights = (heights: Record<string, number>) => {
    const s = useGeometryStore.getState();
    const next = Object.entries(heights).reduce((list, [id, h]) => updateBuilding(list, id, { height_m: h }), s.buildings);
    s.apply(next);
    close();
  };

  const reset = () => (setFile(null), setReport(null), setSizeError(null), mutation.reset());
  const close = () => (reset(), onOpenChange(false));
  return {
    file,
    unit,
    mode,
    report,
    pending: mutation.isPending,
    error: sizeError ?? importErrorText(mutation.error, t),
    setFile: (f: File | null) => (setFile(f), setSizeError(null), mutation.reset()),
    setUnit,
    setMode,
    onSubmit,
    applyHeights,
    undoImport: () => (useGeometryStore.getState().undo(), reset()),
    close,
  };
}
