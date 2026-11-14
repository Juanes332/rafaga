import { useTranslation } from "react-i18next";
import { EmptyState } from "@/components/feedback/EmptyState/EmptyState";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { BaseChangeDialog } from "@/components/geometry/BaseChangeDialog/BaseChangeDialog";
import { BuildingInspector } from "@/components/geometry/BuildingInspector/BuildingInspector";
import { Geometry3D } from "@/components/geometry/Geometry3D/Geometry3D";
import { GeometryIssues } from "@/components/geometry/GeometryIssues/GeometryIssues";
import { GeometrySummary } from "@/components/geometry/GeometrySummary/GeometrySummary";
import { GeometryToolbar } from "@/components/geometry/GeometryToolbar/GeometryToolbar";
import { ImportDialog } from "@/components/geometry/ImportDialog/ImportDialog";
import { PlanCanvas } from "@/components/geometry/PlanCanvas/PlanCanvas";
import { TraceDialog } from "@/components/geometry/TraceDialog/TraceDialog";
import { StepLayout } from "@/components/workspace/StepLayout/StepLayout";
import { Button } from "@/components/ui/button";
import { useGeometryStep } from "./GeometryStep.hook";
import styles from "./GeometryStep.module.css";

/** SCR-06: Paso 2 — Geometría. */
export function GeometryStep() {
  const { t } = useTranslation();
  const s = useGeometryStep();
  const showEmpty = s.empty && !s.readOnly && s.view === "plan";
  const canvas = s.loadError ? (
    <div className={styles.pad}>
      <ErrorNotice error={s.loadError} actionLabel={t("common:retry")} onAction={s.retry} />
    </div>
  ) : s.loading ? (
    <p className={styles.pad}>{t("common:loading")}</p>
  ) : (
    <>
      {s.view === "3d" ? <Geometry3D projectId={s.projectId} /> : <PlanCanvas projectId={s.projectId} readOnly={s.readOnly} />}
      {showEmpty ? (
        <div className={styles.emptyCard}>
          <EmptyState title={t("geometry:emptyTitle")} lead={t("geometry:emptyLead")}>
            <Button onClick={s.startDrawing}>{t("geometry:drawBlock")}</Button>
            <Button variant="outline" onClick={() => s.setImportOpen(true)}>
              {t("geometry:importFile")}
            </Button>
          </EmptyState>
        </div>
      ) : null}
      {s.small ? <p className={styles.small}>{t("geometry:smallScreen")}</p> : null}
    </>
  );
  const inspector = (
    <>
      {s.hasSelection ? <BuildingInspector readOnly={s.readOnly} /> : <GeometrySummary projectId={s.projectId} readOnly={s.readOnly} hint={s.hint} />}
      {s.save.conflict ? (
        <ErrorNotice error={s.save.error} actionLabel={t("geometry:conflict")} onAction={() => void s.save.reload()} />
      ) : s.save.error ? (
        <ErrorNotice error={s.save.error} />
      ) : null}
      <GeometryIssues serverIssues={s.save.serverIssues} />
    </>
  );
  return (
    <>
      <StepLayout
        title={t("geometry:title")}
        toolbar={
          <GeometryToolbar
            readOnly={s.readOnly}
            saving={s.save.saving}
            checking={s.save.checking}
            onSave={s.save.save}
            onCheck={s.save.check}
            onImport={() => s.setImportOpen(true)}
            onTrace={() => s.setTraceOpen(true)}
          />
        }
        canvas={canvas}
        inspector={inspector}
      />
      <ImportDialog projectId={s.projectId} open={s.importOpen} onOpenChange={s.setImportOpen} />
      <TraceDialog projectId={s.projectId} open={s.traceOpen} onOpenChange={s.setTraceOpen} />
      <BaseChangeDialog open={s.save.confirming} onCancel={s.save.cancelConfirm} onConfirm={s.save.confirmSave} />
    </>
  );
}
