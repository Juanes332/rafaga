import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { directionLabel } from "@/lib/format/format.direction";
import type { StudySummary } from "@/types/simulations/simulation.types";
import { useReportForm } from "./ReportForm.hook";
import type { ReportFormProps } from "./ReportForm.types";
import styles from "./ReportForm.module.css";

function useStudyLabel() {
  const { t } = useTranslation();
  return (s: StudySummary) =>
    t("reports:form.studyLabel", {
      name: s.alternative_name,
      kind: t(`reports:kinds.${s.kind}`, { defaultValue: s.kind }),
      directions: (s.directions_deg ?? []).map(directionLabel).join(", "),
    });
}

/** Inspector form for a new report version. */
export function ReportForm(props: ReportFormProps) {
  const { t } = useTranslation();
  const f = useReportForm(props);
  const label = useStudyLabel();
  if (props.readOnly) return <p className={styles.note}>{t("reports:form.readOnly")}</p>;
  return (
    <div className={styles.root}>
      <h2 className={styles.title}>{t("reports:form.title")}</h2>
      {props.studies.length === 0 ? <p className={styles.note}>{t("reports:noResultsReason")}</p> : null}
      {props.studies.length > 0 ? (
        <fieldset className={styles.group}>
          <legend className={styles.legend}>{t("reports:form.studies")}</legend>
          {props.studies.map((s) => (
            <label key={s.id} className={styles.check}>
              <input type="checkbox" checked={f.selected.includes(s.id)} onChange={(e) => f.toggle(s.id, e.target.checked)} />
              <span>{label(s)}</span>
            </label>
          ))}
          {f.selected.length === 0 ? <p className={styles.error}>{t("reports:form.pickOne")}</p> : null}
        </fieldset>
      ) : null}
      {f.selected.length > 1 ? (
        <div className={styles.field}>
          <Label htmlFor="report-baseline">{t("reports:form.baseline")}</Label>
          <Select value={f.baseline} onValueChange={f.setBaseline}>
            <SelectTrigger id="report-baseline" aria-label={t("reports:form.baseline")}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {props.studies.filter((s) => f.selected.includes(s.id)).map((s) => (
                <SelectItem key={s.id} value={s.id}>
                  {label(s)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className={styles.note}>{t("reports:form.baselineHelp")}</p>
        </div>
      ) : null}
      <div className={styles.switchRow}>
        <Switch id="report-comfort" checked={f.comfort} onCheckedChange={f.setComfort} />
        <Label htmlFor="report-comfort">{t("reports:form.comfort")}</Label>
      </div>
      {f.error ? <ErrorNotice error={f.error} /> : null}
      <Button onClick={f.onSubmit} disabled={!f.canSubmit} className={styles.submit}>
        {f.pending ? t("reports:form.submitting") : t("reports:form.submit")}
      </Button>
    </div>
  );
}
