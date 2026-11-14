import { Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { CompareHeader } from "@/components/compare/CompareHeader/CompareHeader";
import { CompareStage } from "@/components/compare/CompareStage/CompareStage";
import { CompareTable } from "@/components/compare/CompareTable/CompareTable";
import { StrategySummary } from "@/components/compare/StrategySummary/StrategySummary";
import { DifferenceList } from "@/components/compare/DifferenceList/DifferenceList";
import { ExportDialog } from "@/components/exports/ExportDialog/ExportDialog";
import { Disclaimer } from "@/components/feedback/Disclaimer/Disclaimer";
import { EmptyState } from "@/components/feedback/EmptyState/EmptyState";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { Button } from "@/components/ui/button";
import { useCompareScreen } from "./CompareScreen.hook";
import styles from "./CompareScreen.module.css";

/** SCR-18: full-screen before/after comparison of two alternatives. */
export function CompareScreen() {
  const { t } = useTranslation();
  const s = useCompareScreen();
  const comparable = s.check?.comparable === true;
  const body = s.empty ? (
    <EmptyState title={t("compare:emptyTitle")} className={styles.empty}>
      <Button asChild>
        <Link to="/projects/$projectId/simulate" params={{ projectId: s.projectId }}>
          {t("compare:goSimulate")}
        </Link>
      </Button>
    </EmptyState>
  ) : s.error ? (
    <ErrorNotice error={s.error} className={styles.notice} />
  ) : s.check && !comparable ? (
    <DifferenceList differences={s.check.differences ?? []} />
  ) : s.ka && s.kb && s.grid ? (
    <CompareStage a={s.ka} b={s.kb} grid={s.grid} buildings={s.buildings} thresholds={s.thresholds} labelA={s.labelA} labelB={s.labelB} />
  ) : (
    <p className={styles.loading}>{t("compare:loading")}</p>
  );
  return (
    <div className={styles.root}>
      <CompareHeader
        projectId={s.projectId}
        options={s.options}
        a={s.a}
        b={s.b}
        direction={s.direction}
        deltaK={s.deltaK}
        zones={s.zones}
        canExport={!s.readOnly && comparable}
        onPick={s.onPick}
        onSwap={s.onSwap}
        onToggleDeltaK={s.toggleDeltaK}
        onToggleZones={s.toggleZones}
        onExport={() => s.setExportOpen(true)}
      />
      <main id="main" className={styles.main}>
        {body}
      </main>
      {comparable && s.ka && s.kb ? (
        <StrategySummary nameA={s.nameA} nameB={s.nameB} ka={s.ka} kb={s.kb} areas={s.areas} comfort={s.comfort} comfortMissing={s.comfortMissing} dkReduction={s.thresholds.dk_reduction} />
      ) : null}
      {comparable ? <CompareTable labelA={s.labelA} labelB={s.labelB} areas={s.areas} comfort={s.comfort} comfortMissing={s.comfortMissing} /> : null}
      <Disclaimer />
      {s.readOnly ? null : (
        <ExportDialog
          open={s.exportOpen}
          onOpenChange={s.setExportOpen}
          resultId={s.a ?? null}
          compareResultId={s.b ?? null}
          defaultLayer={s.deltaK ? "delta_k" : "k"}
        />
      )}
    </div>
  );
}
