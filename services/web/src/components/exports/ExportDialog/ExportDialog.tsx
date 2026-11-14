import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { formatPercent } from "@/lib/format/format.number";
import { jobErrorMessage } from "@/lib/http/error-copy";
import { useExportDialog } from "./ExportDialog.hook";
import type { ExportDialogProps, ExportLayer } from "./ExportDialog.types";
import { DPI_OPTIONS } from "./ExportDialog.utils";
import styles from "./ExportDialog.module.css";

function isJobError(e: unknown): e is { code: string } {
  return typeof e === "object" && e !== null && "code" in e && !(e instanceof Error);
}

/** SCR-19: choose layer and dpi, export on the light lane, download when ready. */
export function ExportDialog(props: ExportDialogProps) {
  const { t } = useTranslation();
  const d = useExportDialog(props);
  const busy = d.phase === "running";
  return (
    <Dialog open={props.open} onOpenChange={d.onOpenChange}>
      <DialogContent closeLabel={t("common:close")}>
        <DialogHeader>
          <DialogTitle>{t("exports:title")}</DialogTitle>
          <DialogDescription>{t("exports:lead", { dpi: d.dpi })}</DialogDescription>
        </DialogHeader>
        {props.resultId === null ? <p className={styles.note}>{t("exports:noResults")}</p> : null}
        <fieldset className={styles.group} disabled={busy || props.resultId === null}>
          <legend className={styles.legend}>{t("exports:layer")}</legend>
          <RadioGroup value={d.layer} onValueChange={(v) => d.setLayer(v as ExportLayer)}>
            {d.layers.map((l) => (
              <div key={l} className={styles.option}>
                <RadioGroupItem id={`export-layer-${l}`} value={l} />
                <Label htmlFor={`export-layer-${l}`}>{t(`exports:layers.${l}`)}</Label>
              </div>
            ))}
          </RadioGroup>
          {!props.compareResultId ? <p className={styles.note}>{t("exports:deltaHint")}</p> : null}
        </fieldset>
        <fieldset className={styles.group} disabled={busy || props.resultId === null}>
          <legend className={styles.legend}>{t("exports:dpi")}</legend>
          <RadioGroup value={String(d.dpi)} onValueChange={(v) => d.setDpi(Number(v))} className={styles.row}>
            {DPI_OPTIONS.map((dpi) => (
              <div key={dpi} className={styles.option}>
                <RadioGroupItem id={`export-dpi-${dpi}`} value={String(dpi)} />
                <Label htmlFor={`export-dpi-${dpi}`}>{t("exports:dpiOption", { dpi })}</Label>
              </div>
            ))}
          </RadioGroup>
        </fieldset>
        <div aria-live="polite" className={styles.status}>
          {busy ? (
            <>
              <p>{t("exports:progress", { percent: formatPercent(d.progress, 0) })}</p>
              <Progress value={d.progress * 100} aria-label={t("exports:running")} />
            </>
          ) : null}
          {d.phase === "ready" ? <p className={styles.ready}>{t("exports:ready")}</p> : null}
        </div>
        {d.error ? <ErrorNotice message={isJobError(d.error) ? jobErrorMessage(d.error.code) : undefined} error={d.error} /> : null}
        <DialogFooter>
          {d.phase === "ready" ? (
            <Button variant="outline" onClick={d.onDownload}>
              {t("exports:download")}
            </Button>
          ) : null}
          <Button onClick={d.onSubmit} disabled={!d.canSubmit}>
            {busy ? t("exports:running") : d.phase === "ready" ? t("exports:again") : t("exports:submit")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
