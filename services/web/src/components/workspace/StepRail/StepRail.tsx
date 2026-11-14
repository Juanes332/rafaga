import { Link } from "@tanstack/react-router";
import { Check, Lock } from "lucide-react";
import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils";
import { useStepRail } from "./StepRail.hook";
import type { StepItem, StepRailProps } from "./StepRail.types";
import styles from "./StepRail.module.css";

const ROUTES = {
  location: "/projects/$projectId/location",
  geometry: "/projects/$projectId/geometry",
  wind: "/projects/$projectId/wind",
  alternatives: "/projects/$projectId/alternatives",
  simulate: "/projects/$projectId/simulate",
  compare: "/projects/$projectId/compare",
} as const;

function StepBody({ step }: { step: StepItem }) {
  const { t } = useTranslation();
  return (
    <>
      <span className={styles.index}>{step.index}</span>
      <span className={styles.text}>
        <span className={styles.full}>{t(`workspace:steps.${step.key}`)}</span>
        <span className={styles.short}>{t(`workspace:steps.short.${step.key}`)}</span>
        {step.state === "done" ? <Check className={styles.check} aria-label={t("workspace:steps.done")} /> : null}
        {step.reasonKey ? (
          <span className={styles.reason}>
            <Lock aria-hidden size={12} /> {t(step.reasonKey)}
          </span>
        ) : null}
      </span>
    </>
  );
}

/** Six-step rail; locked steps stay focusable and announce why. */
export function StepRail({ projectId }: StepRailProps) {
  const { t } = useTranslation();
  const steps = useStepRail(projectId);
  return (
    <nav aria-label={t("workspace:steps.label")} className={styles.root}>
      <ol className={styles.list}>
        {steps.map((step) => (
          <li key={step.key} className={cn(styles.item, styles[step.state])}>
            {step.state === "locked" ? (
              <button type="button" aria-disabled="true" className={styles.link}>
                <StepBody step={step} />
              </button>
            ) : (
              <Link
                to={ROUTES[step.key]}
                params={{ projectId }}
                className={styles.link}
                aria-current={step.state === "current" ? "step" : undefined}
              >
                <StepBody step={step} />
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
