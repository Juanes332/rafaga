import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { exportQueryOptions, fetchExportFile, useCreateExport } from "@/api/exports/exports.queries";
import { settingsQueryOptions } from "@/api/settings/settings.queries";
import { saveBlob } from "@/hooks/download/save-blob";
import type { ExportDialogProps, ExportLayer } from "./ExportDialog.types";
import { availableLayers, exportPhase, type ExportPhase } from "./ExportDialog.utils";

interface UseExportDialog {
  layers: ExportLayer[];
  layer: ExportLayer;
  dpi: number;
  phase: ExportPhase;
  progress: number;
  error: unknown;
  canSubmit: boolean;
  setLayer: (l: ExportLayer) => void;
  setDpi: (d: number) => void;
  onSubmit: () => void;
  onDownload: () => void;
  onOpenChange: (open: boolean) => void;
}

/** Create → poll every 1 s → fetch the blob with the token → save it once. */
export function useExportDialog(p: ExportDialogProps): UseExportDialog {
  const [layer, setLayer] = useState<ExportLayer>(p.defaultLayer ?? "k");
  const [dpi, setDpi] = useState(300);
  const [exportId, setExportId] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<unknown>(null);
  const saved = useRef<string | null>(null);
  const settings = useQuery(settingsQueryOptions());
  const create = useCreateExport();
  const status = useQuery({ ...exportQueryOptions(exportId ?? ""), enabled: exportId !== null });
  const phase = exportPhase(exportId, create.isPending, status.data);

  const download = async (id: string) => {
    try {
      saveBlob(await fetchExportFile(id), `rafaga-${layer}.png`);
    } catch (e) {
      setDownloadError(e);
    }
  };
  useEffect(() => {
    if (phase === "ready" && exportId && saved.current !== exportId) {
      saved.current = exportId;
      void download(exportId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, exportId]);

  const onSubmit = () => {
    if (!p.resultId || !settings.data) return;
    setDownloadError(null);
    const compare = layer === "delta_k" ? (p.compareResultId ?? undefined) : undefined;
    create.mutate(
      { result_id: p.resultId, layer, dpi, thresholds: settings.data.thresholds, compare_result_id: compare },
      { onSuccess: (r) => setExportId(r.export_id) },
    );
  };
  const onOpenChange = (open: boolean) => {
    if (!open) {
      setExportId(null);
      create.reset();
      setDownloadError(null);
    }
    p.onOpenChange(open);
  };

  return {
    layers: availableLayers(p.compareResultId),
    layer,
    dpi,
    phase,
    progress: status.data?.progress ?? 0,
    error: create.error ?? downloadError ?? (phase === "failed" ? status.data?.error ?? status.error : null),
    canSubmit: p.resultId !== null && settings.data !== undefined && phase !== "running",
    setLayer,
    setDpi,
    onSubmit,
    onDownload: () => exportId && void download(exportId),
    onOpenChange,
  };
}
