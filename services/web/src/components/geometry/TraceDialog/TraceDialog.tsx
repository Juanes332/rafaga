import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { ParamField } from "@/components/forms/ParamField/ParamField";
import { TraceImage } from "@/components/geometry/TraceImage/TraceImage";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useTraceDialog } from "./TraceDialog.hook";
import type { TraceDialogProps } from "./TraceDialog.types";
import styles from "./TraceDialog.module.css";

/** SCR-08: a scanned plan as a calibrated background to trace over. */
export function TraceDialog(props: TraceDialogProps) {
  const { t } = useTranslation();
  const d = useTraceDialog(props);
  const pages = d.plan ? Array.from({ length: d.plan.page_count }, (_, i) => i + 1) : [];
  return (
    <Dialog open={props.open} onOpenChange={props.onOpenChange}>
      <DialogContent closeLabel={t("common:close")} className={styles.content}>
        <DialogHeader>
          <DialogTitle>{t("geometry:traceDialog.title")}</DialogTitle>
          <DialogDescription>{t("geometry:traceDialog.lead")}</DialogDescription>
        </DialogHeader>
        <div className={styles.field}>
          <Label htmlFor="trace-file">{t("geometry:traceDialog.file")}</Label>
          <Input id="trace-file" type="file" accept=".png,.jpg,.jpeg,.pdf" disabled={d.uploading} onChange={(e) => d.onFile(e.target.files?.[0])} />
        </div>
        {d.error ? <ErrorNotice error={typeof d.error === "string" ? undefined : d.error} message={typeof d.error === "string" ? d.error : undefined} /> : null}
        {d.plan && d.plan.page_count > 1 ? (
          <div className={styles.field}>
            <Label htmlFor="trace-page">{t("geometry:traceDialog.page")}</Label>
            <Select value={String(d.plan.page)} onValueChange={(v) => d.onPage(Number(v))}>
              <SelectTrigger id="trace-page" className={styles.page}>
                <SelectValue>{d.pageLabel}</SelectValue>
              </SelectTrigger>
              <SelectContent>
                {pages.map((n) => (
                  <SelectItem key={n} value={String(n)}>
                    {t("geometry:traceDialog.pageOf", { page: n, count: d.plan?.page_count })}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        ) : null}
        {d.plan && d.pageUrl ? (
          <>
            <h3 className={styles.title}>{d.calibrated ? t("geometry:traceDialog.ruler") : t("geometry:traceDialog.calibrateTitle")}</h3>
            <p className={styles.muted}>{d.calibrated ? t("geometry:traceDialog.rulerLead") : t("geometry:traceDialog.calibrateLead")}</p>
            <TraceImage url={d.pageUrl} alt={t("geometry:traceDialog.imageAlt", { page: d.plan.page })} points={d.points} onPick={d.onPick} />
            <p role="status" className={styles.status}>
              {d.points.length === 2 ? t("geometry:traceDialog.point2") : d.points.length === 1 ? t("geometry:traceDialog.point1") : t("geometry:traceDialog.pickPoints")}
            </p>
            {d.scaleText ? <p className="num">{d.scaleText}</p> : null}
            {d.rulerText ? <p className={styles.ruler}>{d.rulerText}</p> : null}
            <div className={styles.row}>
              <ParamField id="trace-distance" label={t("geometry:traceDialog.distance")} value={d.distance} unit="m" min={0.1} max={5000} decimals={2} onCommit={d.setDistance} />
              <Button variant="outline" disabled={!d.canCalibrate} onClick={d.calibrate}>
                {t("geometry:traceDialog.apply")}
              </Button>
            </div>
            <ParamField id="trace-opacity" label={t("geometry:traceDialog.opacity")} value={d.plan.opacity ?? 0.5} percent min={0} max={1} step={0.05} slider onCommit={d.onOpacity} />
          </>
        ) : null}
        <DialogFooter>
          <Button onClick={() => props.onOpenChange(false)} disabled={!d.calibrated}>
            {t("geometry:traceDialog.done")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
