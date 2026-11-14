import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { FlowCanvas } from "@/components/results/FlowCanvas/FlowCanvas";
import { KLegend } from "@/components/results/KLegend/KLegend";
import { LawsonLegend } from "@/components/results/LawsonLegend/LawsonLegend";
import { PlanOverlay } from "@/components/results/PlanOverlay/PlanOverlay";
import { usePlanResult } from "./PlanResult.hook";
import type { PlanResultProps } from "./PlanResult.types";
import styles from "./PlanResult.module.css";

/** SCR-14 canvas: K (or speed / Lawson) + particles + zones over the plan. */
export function PlanResult(props: PlanResultProps) {
  const { t } = useTranslation();
  const p = usePlanResult(props);
  if (p.data.error) return <ErrorNotice error={p.data.error} className={styles.notice} />;
  if (!p.data.K || !p.data.paint) return <p className={styles.loading}>{t("results:loading")}</p>;
  const legend =
    p.layer === "lawson" ? (
      <LawsonLegend />
    ) : p.layer === "speed" ? (
      <KLegend kind="speed" max={p.data.speedMax} />
    ) : (
      <KLegend kind="k" marks={[p.thresholds.k_stagnation, p.thresholds.k_accel]} />
    );
  return (
    <FlowCanvas
      paint={p.data.paint}
      paintColor={p.data.paintColor}
      K={p.data.K}
      speed={p.data.speed}
      velocity={p.data.velocity}
      streamlines={p.data.streamlines}
      zoneCodes={p.codes}
      paused={p.paused}
      onTogglePause={p.togglePaused}
      onCellClick={p.onCellClick}
      dxM={p.grid.dx_m}
      legend={legend}
      overlay={(view) => <PlanOverlay view={view} grid={p.grid} buildings={p.buildings} labels={p.labels} section={p.section} />}
    />
  );
}
