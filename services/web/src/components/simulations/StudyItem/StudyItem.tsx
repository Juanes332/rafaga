import { Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import type { StudySummary } from "@/types/simulations/simulation.types";
import { useStudyItem } from "./StudyItem.hook";
import styles from "./StudyItem.module.css";

interface StudyItemProps {
  projectId: string;
  summary: StudySummary;
  readOnly: boolean;
}

/** SCR-13: per-direction progress, phase, ETA, device; cancel, resume, open result. */
export function StudyItem({ projectId, summary, readOnly }: StudyItemProps) {
  const { t } = useTranslation();
  const s = useStudyItem(projectId, summary);
  return (
    <li className={styles.root}>
      <div className={styles.head}>
        <h3 className={styles.title}>{s.title}</h3>
        <span className={styles.status}>{s.statusText}</span>
        <span className={styles.when}>{s.when}</span>
        {s.active && !readOnly ? (
          <Button size="sm" variant="outline" onClick={s.onCancelStudy}>
            {t("simulate:jobs.cancelStudy")}
          </Button>
        ) : null}
      </div>
      <ul className={styles.jobs}>
        {s.jobs.map((j) => (
          <li key={j.id} className={styles.job}>
            <span className={styles.dir}>{j.dir}</span>
            <Progress value={j.percent} aria-label={t("simulate:jobs.progress", { dir: j.dir })} className={styles.bar} />
            <span className={styles.pct}>{j.percentText}</span>
            <span className={styles.jobStatus}>{j.detail || j.statusText}</span>
            <span className={styles.actions}>
              {j.resultId ? (
                <Link to="/projects/$projectId/results/$resultId" params={{ projectId, resultId: j.resultId }}>
                  {t("simulate:jobs.viewResult", { dir: j.dir })}
                </Link>
              ) : null}
              {j.canCancel && !readOnly && s.jobs.length > 1 ? (
                <Button size="sm" variant="ghost" onClick={() => s.onCancelJob(j.id)}>
                  {t("simulate:jobs.cancelJob", { dir: j.dir })}
                </Button>
              ) : null}
              {j.canRetry && !readOnly ? (
                <Button size="sm" variant="secondary" onClick={() => s.onRetry(j.id)}>
                  {t("simulate:jobs.retry", { dir: j.dir })}
                </Button>
              ) : null}
            </span>
            {j.error ? <p className={styles.error}>{j.error}</p> : null}
          </li>
        ))}
      </ul>
      {s.error ? <ErrorNotice error={s.error} /> : null}
    </li>
  );
}
