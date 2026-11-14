import { Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { DirectionPicker } from "@/components/simulations/DirectionPicker/DirectionPicker";
import { JobsList } from "@/components/simulations/JobsList/JobsList";
import { SimulationForm } from "@/components/simulations/SimulationForm/SimulationForm";
import { StepLayout } from "@/components/workspace/StepLayout/StepLayout";
import { useSimulateStep } from "./SimulateStep.hook";
import styles from "./SimulateStep.module.css";

/** SCR-12 + SCR-13 — Paso 5, Simular: choose directions, estimate, launch, follow progress. */
export function SimulateStep() {
  const { t } = useTranslation();
  const s = useSimulateStep();
  if (!s.loading && !s.hasLocation) {
    return (
      <StepLayout
        title={t("simulate:title")}
        canvas={
          <div className={styles.locked}>
            <ErrorNotice message={t("simulate:locked")} />
            <Link to="/projects/$projectId/location" params={{ projectId: s.projectId }}>
              {t("wind:goLocation")}
            </Link>
          </div>
        }
      />
    );
  }
  const canvas = (
    <div className={styles.canvas}>
      {!s.readOnly ? <DirectionPicker sectors={s.sectors} disabled={s.readOnly} /> : null}
      <JobsList projectId={s.projectId} readOnly={s.readOnly} />
    </div>
  );
  const inspector = s.readOnly ? undefined : <SimulationForm projectId={s.projectId} alternatives={s.alternatives} />;
  return <StepLayout title={t("simulate:title")} canvas={canvas} inspector={inspector} />;
}
