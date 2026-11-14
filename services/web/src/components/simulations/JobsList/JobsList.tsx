import { Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { EmptyState } from "@/components/feedback/EmptyState/EmptyState";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { StudyItem } from "@/components/simulations/StudyItem/StudyItem";
import { useJobsList } from "./JobsList.hook";
import styles from "./JobsList.module.css";

/** Every simulation of the project with live progress. */
export function JobsList({ projectId, readOnly }: { projectId: string; readOnly: boolean }) {
  const { t } = useTranslation();
  const l = useJobsList(projectId);
  return (
    <section className={styles.root} aria-labelledby="jobs-title">
      <div className={styles.head}>
        <h2 id="jobs-title" className={styles.title}>
          {t("simulate:jobs.title")}
        </h2>
        {l.canCompare ? (
          <Link to="/projects/$projectId/compare" params={{ projectId }}>
            {t("simulate:jobs.compare")}
          </Link>
        ) : null}
        <Link to="/projects/$projectId/reports" params={{ projectId }}>
          {t("simulate:jobs.reports")}
        </Link>
      </div>
      {l.error ? <ErrorNotice error={l.error} /> : null}
      {!l.loading && l.studies.length === 0 ? <EmptyState className={styles.empty} title={t("simulate:jobs.empty")} /> : null}
      <ul className={styles.list}>
        {l.studies.map((s) => (
          <StudyItem key={s.id} projectId={projectId} summary={s} readOnly={readOnly} />
        ))}
      </ul>
    </section>
  );
}
