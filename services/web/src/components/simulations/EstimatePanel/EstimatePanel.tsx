import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { formatDuration } from "@/lib/format/format.date";
import type { EstimatePanelProps } from "./EstimatePanel.types";
import { formatBytes, formatDx, formatNodes } from "./EstimatePanel.utils";
import styles from "./EstimatePanel.module.css";

/** Size, memory against budget and ETA before launching (FR-56, ADR-10). */
export function EstimatePanel({ estimate: e, loading, autoCoarsen, onUseProposed, onAutoCoarsen }: EstimatePanelProps) {
  const { t } = useTranslation();
  if (!e) return <p className={styles.muted}>{loading ? t("simulate:estimate.loading") : null}</p>;
  const offline = e.rejected_reason === "solver_offline";
  const memory = { used: formatBytes(e.memory_bytes), budget: formatBytes(e.budget_bytes) };
  return (
    <section className={styles.root} aria-labelledby="estimate-title" aria-busy={loading}>
      <h2 id="estimate-title" className={styles.title}>
        {t("simulate:estimate.title")}
      </h2>
      {offline ? <p className={styles.warn}>{t("simulate:estimate.solverOffline")}</p> : null}
      <dl className={styles.list}>
        <div className={styles.row}>
          <dt>{t("simulate:estimate.nodes")}</dt>
          <dd>{formatNodes(e.nodes)}</dd>
        </div>
        {!offline ? (
          <div className={styles.row}>
            <dt>{t("simulate:estimate.memory")}</dt>
            <dd>{t("simulate:estimate.memoryOf", memory)}</dd>
          </div>
        ) : null}
        <div className={styles.row}>
          <dt>{t("simulate:estimate.eta")}</dt>
          <dd>{formatDuration(e.eta_seconds)}</dd>
        </div>
        <div className={styles.row}>
          <dt>{t("simulate:estimate.device")}</dt>
          <dd>{t(`simulate:form.devices.${e.device}`)}</dd>
        </div>
      </dl>
      {!offline && e.budget_bytes > 0 ? (
        <Progress value={Math.min(100, (e.memory_bytes / e.budget_bytes) * 100)} aria-label={t("simulate:estimate.memory")} className={styles.bar} />
      ) : null}
      {!offline && e.fits ? <p className={styles.muted}>{t("simulate:estimate.fits")}</p> : null}
      {!offline && !e.fits ? (
        <div className={styles.tooLarge} role="alert">
          <p>{t("simulate:estimate.tooLarge", memory)}</p>
          {e.proposed_dx_m ? (
            <Button size="sm" variant="secondary" onClick={() => onUseProposed(e.proposed_dx_m as number)}>
              {t("simulate:estimate.useProposed", { dx: formatDx(e.proposed_dx_m) })}
            </Button>
          ) : null}
          <div className={styles.switchRow}>
            <Switch id="auto-coarsen" checked={autoCoarsen} onCheckedChange={onAutoCoarsen} />
            <Label htmlFor="auto-coarsen">{t("simulate:estimate.autoCoarsen")}</Label>
          </div>
        </div>
      ) : null}
    </section>
  );
}
