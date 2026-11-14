import { useTranslation } from "react-i18next";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { formatDuration } from "@/lib/format/format.date";
import { formatNodes } from "@/components/simulations/EstimatePanel/EstimatePanel.utils";
import { NFR03_CPU_MAX_NODES } from "./CpuWarningDialog.utils";
import type { CpuWarningDialogProps } from "./CpuWarningDialog.types";

/** NFR-03: a 3D run without GPU must be confirmed after seeing how long it will take. */
export function CpuWarningDialog({ open, etaSeconds, nodes, onCancel, onConfirm }: CpuWarningDialogProps) {
  const { t } = useTranslation();
  return (
    <AlertDialog open={open} onOpenChange={(o) => !o && onCancel()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{t("simulate:cpuWarning.title")}</AlertDialogTitle>
          <AlertDialogDescription>{t("simulate:cpuWarning.body")}</AlertDialogDescription>
        </AlertDialogHeader>
        <div role="status">
          <p>{t("simulate:cpuWarning.eta", { value: formatDuration(etaSeconds) })}</p>
          <p>{t("simulate:cpuWarning.nodes", { value: formatNodes(nodes) })}</p>
          <p>{t("simulate:cpuWarning.limit", { value: formatNodes(NFR03_CPU_MAX_NODES) })}</p>
        </div>
        <AlertDialogFooter>
          <AlertDialogCancel autoFocus>{t("common:cancel")}</AlertDialogCancel>
          <AlertDialogAction onClick={onConfirm}>{t("simulate:cpuWarning.confirm")}</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
