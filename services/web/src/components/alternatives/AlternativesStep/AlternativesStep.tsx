import { Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { AlternativesList } from "@/components/alternatives/AlternativesList/AlternativesList";
import { EmptyState } from "@/components/feedback/EmptyState/EmptyState";
import { ElementsList } from "@/components/facades/ElementsList/ElementsList";
import { FacadeEditor } from "@/components/facades/FacadeEditor/FacadeEditor";
import { FacadePlan } from "@/components/facades/FacadePlan/FacadePlan";
import { StepLayout } from "@/components/workspace/StepLayout/StepLayout";
import { useAlternativesStep, type UseAlternativesStep } from "./AlternativesStep.hook";
import styles from "./AlternativesStep.module.css";

function Inspector({ s }: { s: UseAlternativesStep }) {
  const { t } = useTranslation();
  const c = s.current;
  return (
    <>
      <AlternativesList projectId={s.projectId} alternatives={s.alternatives} selectedId={c?.id ?? null} readOnly={s.readOnly} onSelect={s.selectAlternative} />
      {s.onlyBase ? <EmptyState className={styles.empty} title={t("alternatives:emptyTitle")} /> : null}
      {c?.is_base ? <p className={`reading ${styles.note}`}>{t("alternatives:list.baseNote")}</p> : null}
      {c && !c.is_base && s.edge ? (
        <FacadeEditor
          projectId={s.projectId}
          alternativeId={c.id}
          edge={s.edge}
          buildingName={s.buildingName(s.edge.buildingId)}
          element={s.edgeElement}
          readOnly={s.readOnly}
        />
      ) : null}
      {c && !c.is_base && !s.edge ? <p className={styles.note}>{t("alternatives:editor.noSelection")}</p> : null}
      {c && !c.is_base ? <ElementsList elements={s.elements} buildingName={s.buildingName} onSelect={s.selectEdge} /> : null}
    </>
  );
}

function Canvas({ s }: { s: UseAlternativesStep }) {
  const { t } = useTranslation();
  if (!s.loading && s.buildings.length === 0) {
    return (
      <EmptyState className={styles.pad} title={t("alternatives:noBuildingsTitle")}>
        <Link to="/projects/$projectId/geometry" params={{ projectId: s.projectId }}>
          {t("alternatives:goGeometry")}
        </Link>
      </EmptyState>
    );
  }
  const interactive = Boolean(s.current && !s.current.is_base && !s.readOnly);
  return (
    <div className={styles.canvas}>
      <p className={styles.hint}>{interactive ? t("alternatives:plan.hint") : t("alternatives:plan.baseHint")}</p>
      <FacadePlan buildings={s.buildings} elements={s.elements} selected={s.edge} interactive={interactive} onSelect={s.selectEdge} />
    </div>
  );
}

/** SCR-11 — Paso 4, Alternativas y fachadas. */
export function AlternativesStep() {
  const { t } = useTranslation();
  const s = useAlternativesStep();
  return <StepLayout title={t("alternatives:title")} canvas={<Canvas s={s} />} inspector={<Inspector s={s} />} />;
}
