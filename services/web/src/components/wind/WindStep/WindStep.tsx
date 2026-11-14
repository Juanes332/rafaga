import { Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { EmptyState } from "@/components/feedback/EmptyState/EmptyState";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { Button } from "@/components/ui/button";
import { SectorTable } from "@/components/wind/SectorTable/SectorTable";
import { WindPanel } from "@/components/wind/WindPanel/WindPanel";
import { WindRose } from "@/components/wind/WindRose/WindRose";
import { RoseLegend } from "@/components/wind/WindRose/RoseLegend";
import { StepLayout } from "@/components/workspace/StepLayout/StepLayout";
import { directionLabel } from "@/lib/format/format.direction";
import { formatPercent, formatUnit } from "@/lib/format/format.number";
import { useWindStep, type UseWindStep } from "./WindStep.hook";
import styles from "./WindStep.module.css";

function WindCanvas({ s }: { s: UseWindStep }) {
  const { t } = useTranslation();
  const w = s.wind;
  if (!w) {
    return (
      <div className={styles.pad}>
        {s.fetchError ? <ErrorNotice error={s.fetchError} actionLabel={t("wind:offline.manual")} onAction={s.onManual} /> : null}
        <EmptyState title={t("wind:emptyTitle")} lead={t("wind:emptyLead")}>
          {!s.readOnly ? (
            <>
              <Button disabled={s.fetching} onClick={s.onFetch}>
                {s.fetching ? t("wind:fetching") : t("wind:fetch")}
              </Button>
              <Button variant="outline" onClick={s.onManual}>
                {t("wind:offline.manual")}
              </Button>
            </>
          ) : null}
        </EmptyState>
      </div>
    );
  }
  const showRose = !s.manual && w.rose;
  return (
    <div className={styles.canvas}>
      {s.fetchError ? <ErrorNotice error={s.fetchError} actionLabel={t("wind:offline.manual")} onAction={s.onManual} /> : null}
      <div className={styles.roseCol}>
        <WindRose sectors={showRose ? (w.rose?.sectors ?? null) : null} manualDeg={showRose ? null : w.manual_direction_deg} size={400} />
        {showRose && w.rose ? <RoseLegend calm={formatPercent(w.rose.calm_fraction)} /> : null}
        {!showRose && w.manual_direction_deg != null ? (
          <p className={styles.manual}>
            {t("wind:manual.summary", { dir: directionLabel(w.manual_direction_deg), speed: formatUnit(w.manual_u10_ms, 1, "m/s") })}
          </p>
        ) : null}
      </div>
      {showRose && w.rose ? (
        <div className={styles.tableCol}>
          <SectorTable sectors={w.rose.sectors} />
        </div>
      ) : null}
    </div>
  );
}

/** SCR-10 — Paso 3, Viento. */
export function WindStep() {
  const { t } = useTranslation();
  const s = useWindStep();
  if (!s.loading && !s.hasLocation) {
    return (
      <StepLayout
        title={t("wind:title")}
        canvas={
          <div className={styles.pad}>
            <ErrorNotice message={t("wind:locked")} />
            <Link to="/projects/$projectId/location" params={{ projectId: s.projectId }}>
              {t("wind:goLocation")}
            </Link>
          </div>
        }
      />
    );
  }
  return <StepLayout title={t("wind:title")} canvas={<WindCanvas s={s} />} inspector={<WindPanel {...s} />} />;
}
