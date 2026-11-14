import { lazy, Suspense } from "react";
import { Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { Disclaimer } from "@/components/feedback/Disclaimer/Disclaimer";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { ExportDialog } from "@/components/exports/ExportDialog/ExportDialog";
import { PlanResult } from "@/components/results/PlanResult/PlanResult";
import { ResultInspector } from "@/components/results/ResultInspector/ResultInspector";
import { ResultsToolbar } from "@/components/results/ResultsToolbar/ResultsToolbar";
import { SectionResult } from "@/components/results/SectionResult/SectionResult";
import { StepLayout } from "@/components/workspace/StepLayout/StepLayout";
import { useResultsStep } from "./ResultsStep.hook";
import styles from "./ResultsStep.module.css";

// three.js only loads when someone opens a 3D result.
const ResultsViewer3D = lazy(() => import("@/components/viewer3d/ResultsViewer3D/ResultsViewer3D"));

/** SCR-14..17: results in plan with particles, zones, Lawson, section and 3D. */
export function ResultsStep() {
  const { t } = useTranslation();
  const s = useResultsStep();
  if (s.error || (!s.isLoading && !s.result)) {
    return (
      <div className={styles.missing}>
        <ErrorNotice error={s.error} />
        <Link to="/projects/$projectId/simulate" params={{ projectId: s.projectId }}>
          {t("results:goSimulate")}
        </Link>
      </div>
    );
  }
  if (!s.result) return <p className={styles.loading}>{t("results:loading")}</p>;
  const r = s.result;
  const canvas =
    r.kind === "section2d" ? (
      <SectionResult result={r} />
    ) : r.kind === "volume3d" && s.view3d ? (
      <Suspense fallback={<p className={styles.loading}>{t("results:view3d.loading")}</p>}>
        <ResultsViewer3D resultId={r.id} />
      </Suspense>
    ) : (
      <PlanResult projectId={s.projectId} result={r} />
    );
  return (
    <>
      <StepLayout
        title={t("results:title")}
        toolbar={<ResultsToolbar resultId={r.id} kind={r.kind} directions={s.directions} readOnly={s.readOnly} onDirection={s.onDirection} />}
        canvas={canvas}
        inspector={
          <ResultInspector
            projectId={s.projectId}
            result={r}
            alternativeName={s.alternativeName}
            alternativeId={s.alternativeId}
            readOnly={s.readOnly}
            onExport={() => s.setExportOpen(true)}
          />
        }
        footer={<Disclaimer />}
      />
      {s.readOnly ? null : <ExportDialog open={s.exportOpen} onOpenChange={s.setExportOpen} resultId={r.id} defaultLayer="k" />}
    </>
  );
}
