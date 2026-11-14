import type { Export } from "@/types/exports/export.types";
import type { ExportLayer } from "./ExportDialog.types";

export const DPI_OPTIONS = [300, 450, 600] as const;

/** ΔK needs a second, comparable result. */
export function availableLayers(compareResultId: string | null | undefined): ExportLayer[] {
  return compareResultId ? ["k", "zones", "speed", "delta_k", "lawson"] : ["k", "zones", "speed", "lawson"];
}

export type ExportPhase = "idle" | "running" | "ready" | "failed";

export function exportPhase(exportId: string | null, pending: boolean, status: Export | undefined): ExportPhase {
  if (pending) return "running";
  if (!exportId) return "idle";
  if (!status || status.status === "queued" || status.status === "running") return "running";
  return status.status === "completed" && status.file_ready ? "ready" : "failed";
}
