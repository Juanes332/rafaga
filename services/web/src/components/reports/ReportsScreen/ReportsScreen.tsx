import { useTranslation } from "react-i18next";
import { EmptyState } from "@/components/feedback/EmptyState/EmptyState";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { ReportForm } from "@/components/reports/ReportForm/ReportForm";
import { ReportVersionsTable } from "@/components/reports/ReportVersionsTable/ReportVersionsTable";
import { Button } from "@/components/ui/button";
import { StepLayout } from "@/components/workspace/StepLayout/StepLayout";
import { useReportsScreen } from "./ReportsScreen.hook";
import styles from "./ReportsScreen.module.css";

/** SCR-20: PDF report versions of the project. */
export function ReportsScreen() {
  const { t } = useTranslation();
  const s = useReportsScreen();
  const noResults = !s.loading && s.studies.length === 0 && s.reports.length === 0;
  const canvas = (
    <div className={styles.canvas}>
      <h2 className={styles.title}>{t("reports:title")}</h2>
      {s.error ? <ErrorNotice error={s.error} /> : null}
      {noResults ? (
        <EmptyState title={t("reports:emptyTitle")} lead={t("reports:emptyLead")}>
          <Button disabled aria-describedby="reports-reason">
            {t("reports:form.submit")}
          </Button>
          <p id="reports-reason" className={styles.reason}>
            {t("reports:noResultsReason")}
          </p>
        </EmptyState>
      ) : null}
      {!noResults && s.reports.length === 0 && !s.loading ? <p className={styles.reason}>{t("reports:noVersions")}</p> : null}
      {s.reports.length > 0 ? (
        <section aria-label={t("reports:versions")}>
          <ReportVersionsTable reports={s.reports} onDownload={s.onDownload} />
        </section>
      ) : null}
    </div>
  );
  return (
    <StepLayout
      title={t("reports:title")}
      canvas={canvas}
      inspector={noResults ? undefined : <ReportForm projectId={s.projectId} studies={s.studies} readOnly={s.readOnly} />}
    />
  );
}
