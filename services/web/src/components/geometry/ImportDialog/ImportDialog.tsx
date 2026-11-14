import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { ImportReportView } from "@/components/geometry/ImportReportView/ImportReportView";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { ImportUnit } from "@/api/geometry/geometry.queries";
import { useImportDialog } from "./ImportDialog.hook";
import type { ImportDialogProps } from "./ImportDialog.types";
import { IMPORT_ACCEPT } from "./ImportDialog.utils";
import styles from "./ImportDialog.module.css";

const UNITS: ImportUnit[] = ["auto", "m", "cm", "mm", "ft"];

/** SCR-07: import DXF/STL/OBJ/IFC and review what came in. */
export function ImportDialog(props: ImportDialogProps) {
  const { t } = useTranslation();
  const d = useImportDialog(props);
  return (
    <Dialog open={props.open} onOpenChange={(o) => (o ? props.onOpenChange(true) : d.close())}>
      <DialogContent closeLabel={t("common:close")} className={styles.content}>
        <DialogHeader>
          <DialogTitle>{d.report ? t("geometry:import.reportTitle") : t("geometry:import.title")}</DialogTitle>
          <DialogDescription>{d.report ? null : t("geometry:import.lead")}</DialogDescription>
        </DialogHeader>
        {d.report ? (
          <ImportReportView report={d.report} onApplyHeights={d.applyHeights} onUndo={d.undoImport} onDone={d.close} />
        ) : (
          <form className={styles.form} onSubmit={d.onSubmit}>
            <div className={styles.field}>
              <Label htmlFor="import-file">{t("geometry:import.file")}</Label>
              <Input id="import-file" type="file" accept={IMPORT_ACCEPT} onChange={(e) => d.setFile(e.target.files?.[0] ?? null)} />
            </div>
            <div className={styles.field}>
              <Label htmlFor="import-unit">{t("geometry:import.unit")}</Label>
              <Select value={d.unit} onValueChange={(v) => d.setUnit(v as ImportUnit)}>
                <SelectTrigger id="import-unit">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {UNITS.map((u) => (
                    <SelectItem key={u} value={u}>
                      {t(`geometry:import.units.${u}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <fieldset className={styles.fieldset}>
              <legend className={styles.legend}>{t("geometry:import.mode")}</legend>
              <RadioGroup value={d.mode} onValueChange={(v) => d.setMode(v as "append" | "replace")}>
                {(["append", "replace"] as const).map((m) => (
                  <div key={m} className={styles.radio}>
                    <RadioGroupItem id={`import-${m}`} value={m} />
                    <Label htmlFor={`import-${m}`}>{t(`geometry:import.${m}`)}</Label>
                  </div>
                ))}
              </RadioGroup>
            </fieldset>
            {d.error ? <ErrorNotice message={d.error} /> : null}
            <DialogFooter>
              <Button variant="outline" onClick={d.close}>
                {t("common:cancel")}
              </Button>
              <Button type="submit" disabled={!d.file || d.pending}>
                {d.pending ? t("geometry:import.submitting") : t("geometry:import.submit")}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
