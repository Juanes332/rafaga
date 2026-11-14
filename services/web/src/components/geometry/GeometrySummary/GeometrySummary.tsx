import { useTranslation } from "react-i18next";
import { ParamField } from "@/components/forms/ParamField/ParamField";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useGeometrySummary } from "./GeometrySummary.hook";
import styles from "./GeometrySummary.module.css";

interface GeometrySummaryProps {
  projectId: string;
  readOnly: boolean;
  hint: string;
}

/** Inspector with nothing selected: what is on the plan and how drawing behaves. */
export function GeometrySummary({ projectId, readOnly, hint }: GeometrySummaryProps) {
  const { t } = useTranslation();
  const s = useGeometrySummary(projectId);
  return (
    <section className={styles.root}>
      <h2 className={styles.title}>{t("geometry:title")}</h2>
      <p className="num">{s.summary}</p>
      <p className={styles.hint}>{readOnly ? t("geometry:inspector.none") : hint}</p>
      {!readOnly ? (
        <div className={styles.field}>
          <Label htmlFor="snap-step">{t("geometry:inspector.snap")}</Label>
          <Select value={s.snapValue} onValueChange={s.onSnap}>
            <SelectTrigger id="snap-step">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {s.snapOptions.map((o) => (
                <SelectItem key={o.value} value={o.value}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      ) : null}
      {s.background && !readOnly ? (
        <div className={styles.field}>
          <h3 className={styles.subtitle}>{t("geometry:inspector.background")}</h3>
          <ParamField
            id="bg-opacity"
            label={t("geometry:inspector.opacity")}
            value={s.background.opacity ?? 0.5}
            percent
            min={0}
            max={1}
            step={0.05}
            slider
            onCommit={s.onOpacity}
          />
          <Button variant="ghost" size="sm" className={styles.remove} onClick={s.onRemoveBackground}>
            {t("geometry:inspector.removeBackground")}
          </Button>
        </div>
      ) : null}
    </section>
  );
}
