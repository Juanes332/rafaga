import { Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { EmptyState } from "@/components/feedback/EmptyState/EmptyState";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { ParamField } from "@/components/forms/ParamField/ParamField";
import { CoordinateForm } from "@/components/location/CoordinateForm/CoordinateForm";
import { LocationMap } from "@/components/location/LocationMap/LocationMap";
import { LocationSummary } from "@/components/location/LocationSummary/LocationSummary";
import { ManualElevation } from "@/components/location/ManualElevation/ManualElevation";
import { PlaceSearch } from "@/components/location/PlaceSearch/PlaceSearch";
import { StepLayout } from "@/components/workspace/StepLayout/StepLayout";
import { useLocationStep } from "./LocationStep.hook";
import styles from "./LocationStep.module.css";

/** SCR-05 — Paso 1, Proyecto: where the project is. */
export function LocationStep() {
  const { t } = useTranslation();
  const s = useLocationStep();
  const p = s.project;
  const inspector = (
    <>
      {!s.hasLocation ? <EmptyState className={styles.empty} title={t("location:emptyTitle")} lead={t("location:emptyLead")} /> : null}
      {!s.readOnly ? <PlaceSearch onPick={s.onPick} /> : null}
      {!s.readOnly ? <CoordinateForm lat={p?.lat ?? null} lon={p?.lon ?? null} pending={s.pending} onSubmit={s.onPick} /> : null}
      {s.needsElevation ? <ManualElevation pending={s.pending} onSubmit={s.onManualElevation} /> : null}
      {s.error ? <ErrorNotice error={s.error} /> : null}
      {p && s.hasLocation ? <LocationSummary project={p} /> : null}
      {p ? (
        <ParamField
          id="analysis-height"
          label={t("location:height.label")}
          unit="m"
          min={0.5}
          max={3}
          step={0.1}
          slider
          decimals={1}
          defaultValue={1.5}
          value={p.analysis_height_m}
          help={t("location:height.help")}
          disabled={s.readOnly}
          onCommit={s.onHeight}
        />
      ) : null}
      {s.hasLocation ? (
        <Link className={styles.next} to="/projects/$projectId/geometry" params={{ projectId: s.projectId }}>
          {t("location:next")}
        </Link>
      ) : null}
    </>
  );
  return (
    <StepLayout
      title={t("location:title")}
      canvas={<LocationMap lat={p?.lat ?? null} lon={p?.lon ?? null} onPick={s.onPick} />}
      inspector={inspector}
    />
  );
}
