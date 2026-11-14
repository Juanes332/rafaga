import { Download } from "lucide-react";
import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { LawsonPanel } from "@/components/results/LawsonPanel/LawsonPanel";
import { SectionPanel } from "@/components/results/SectionPanel/SectionPanel";
import { ZoneLegend } from "@/components/results/ZoneLegend/ZoneLegend";
import { Button } from "@/components/ui/button";
import { directionLabel } from "@/lib/format/format.direction";
import { formatNumber, formatUnit } from "@/lib/format/format.number";
import { useResultInspector } from "./ResultInspector.hook";
import type { ResultInspectorProps } from "./ResultInspector.types";
import styles from "./ResultInspector.module.css";

/** Right column of the results view. */
export function ResultInspector(p: ResultInspectorProps) {
  const { t } = useTranslation();
  const r = useResultInspector(p);
  const s = p.result.stats;
  return (
    <>
      <header className={styles.head}>
        <h2 className={styles.title}>{t("results:inspectorTitle")}</h2>
        <p className={styles.sub}>{t("results:summary", { alternative: p.alternativeName, direction: directionLabel(p.result.direction_deg) })}</p>
      </header>
      <dl className={styles.stats}>
        <dt>{t("results:stats.kMean")}</dt>
        <dd>{formatNumber(s.k_mean, 2)}</dd>
        <dt>{t("results:stats.kMax")}</dt>
        <dd>{formatNumber(s.k_max, 2)}</dd>
        <dt>{t("results:stats.cell")}</dt>
        <dd>{formatUnit(p.result.dx_m, 1, "m")}</dd>
        <dt>{t("results:stats.device")}</dt>
        <dd>{p.result.device.toUpperCase()}</dd>
      </dl>
      {p.result.convergence && !p.result.convergence.converged ? <p className={styles.warn}>{t("results:stats.notConverged")}</p> : null}
      {r.warnings.length > 0 ? (
        <ul className={styles.notes} aria-label={t("results:warnings.title")}>
          {r.warnings.map((w) => (
            <li key={w} className={styles.warn}>{t(`results:warnings.${w}`)}</li>
          ))}
        </ul>
      ) : null}
      {r.showSection ? <SectionPanel projectId={p.projectId} alternativeId={p.alternativeId} dxM={p.result.dx_m} directionDeg={p.result.direction_deg} /> : null}
      {r.isPlan && r.zones ? <ZoneLegend items={r.zoneItems} /> : null}
      {r.zonesError ? <ErrorNotice error={r.zonesError} /> : null}
      {r.showLawson && p.result.study_id ? <LawsonPanel studyId={p.result.study_id} readOnly={p.readOnly} /> : null}
      {p.readOnly ? null : (
        <Button variant="outline" className={styles.export} onClick={p.onExport}>
          <Download aria-hidden />
          {t("results:export")}
        </Button>
      )}
    </>
  );
}
