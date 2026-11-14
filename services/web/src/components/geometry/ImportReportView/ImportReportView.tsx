import { useTranslation } from "react-i18next";
import { ParamField } from "@/components/forms/ParamField/ParamField";
import { Button } from "@/components/ui/button";
import { DEFAULT_HEIGHT_M, HEIGHT_RANGE } from "@/engines/geometry/buildings";
import type { ImportReport } from "@/types/geometry/geometry.types";
import { useImportReportView } from "./ImportReportView.hook";
import styles from "./ImportReportView.module.css";

interface ImportReportViewProps {
  report: ImportReport;
  onApplyHeights: (heights: Record<string, number>) => void;
  onUndo: () => void;
  onDone: () => void;
}

/** What came in, what needs a height, what was skipped and why. */
export function ImportReportView({ report, onApplyHeights, onUndo, onDone }: ImportReportViewProps) {
  const { t } = useTranslation();
  const v = useImportReportView(report);
  return (
    <div className={styles.root}>
      <p role="status">
        {t("geometry:import.added", { count: report.buildings_added })} {t("geometry:import.detectedUnit", { unit: v.unitText })}
      </p>
      <p className={styles.muted}>{t("geometry:import.unitWrong")}</p>
      {v.missing.length > 0 ? (
        <section className={styles.section}>
          <h3 className={styles.title}>{t("geometry:import.missingTitle")}</h3>
          <p className={styles.muted}>{t("geometry:import.missingLead")}</p>
          {v.missing.map((m) => (
            <ParamField
              key={m.id}
              id={`h-${m.id}`}
              label={m.name}
              value={v.heights[m.id] ?? null}
              unit="m"
              min={HEIGHT_RANGE[0]}
              max={HEIGHT_RANGE[1]}
              defaultValue={DEFAULT_HEIGHT_M}
              onCommit={(h) => v.setHeight(m.id, h)}
            />
          ))}
        </section>
      ) : null}
      {report.ignored.length > 0 ? (
        <section className={styles.section}>
          <h3 className={styles.title}>{t("geometry:import.ignoredTitle")}</h3>
          <ul className={styles.list}>
            {report.ignored.map((i, n) => (
              <li key={n}>
                <strong>{i.entity}</strong> {v.reasonText(i.reason)}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      <div className={styles.actions}>
        <Button variant="ghost" onClick={onUndo}>
          {t("geometry:import.undo")}
        </Button>
        {v.missing.length > 0 ? (
          <Button disabled={!v.allSet} onClick={() => onApplyHeights(v.heights)}>
            {t("geometry:import.applyHeights")}
          </Button>
        ) : (
          <Button onClick={onDone}>{t("geometry:import.done")}</Button>
        )}
      </div>
    </div>
  );
}
