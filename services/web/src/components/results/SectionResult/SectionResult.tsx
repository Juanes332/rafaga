import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { FieldRaster } from "@/components/results/FieldRaster/FieldRaster";
import { KLegend } from "@/components/results/KLegend/KLegend";
import { formatNumber } from "@/lib/format/format.number";
import type { Result } from "@/types/results/result.types";
import { useSectionResult } from "./SectionResult.hook";
import styles from "./SectionResult.module.css";

/** SCR-17 display: speed along the section with height and distance axes. */
export function SectionResult({ result }: { result: Result }) {
  const { t } = useTranslation();
  const s = useSectionResult(result);
  return (
    <div className={styles.root}>
      <div ref={s.box} className={styles.stage} role="img" aria-label={t("results:section.viewLabel")}>
        {s.error ? <ErrorNotice error={s.error} /> : null}
        {s.field ? <FieldRaster field={s.field} color={s.color} view={s.view} width={s.size.width} height={s.size.height} className={styles.layer} /> : null}
        <svg className={styles.layer} width={s.size.width} height={s.size.height} aria-hidden>
          <line x1={s.view.ox} x2={s.view.ox} y1={s.view.oy} y2={s.bottom} className={styles.axis} />
          <line x1={s.view.ox} x2={s.size.width - 16} y1={s.bottom} y2={s.bottom} className={styles.axis} />
          {s.zTicks.map((tk) => (
            <text key={`z${tk.v}`} x={s.view.ox - 8} y={tk.y + 4} textAnchor="end" className={styles.tick}>
              {formatNumber(tk.v, 0)}
            </text>
          ))}
          {s.sTicks.map((tk) => (
            <text key={`s${tk.v}`} x={tk.x} y={s.bottom + 16} textAnchor="middle" className={styles.tick}>
              {formatNumber(tk.v, 0)}
            </text>
          ))}
          <text x={12} y={s.view.oy + 4} className={styles.axisLabel} transform={`rotate(-90 12 ${s.view.oy + 4})`} textAnchor="end">
            {t("results:section.heightAxis")}
          </text>
          <text x={s.view.ox} y={s.bottom + 34} className={styles.axisLabel}>
            {t("results:section.distanceAxis")}
          </text>
        </svg>
      </div>
      <div className={styles.legend}>
        <KLegend kind="speed" max={s.max} />
      </div>
    </div>
  );
}
