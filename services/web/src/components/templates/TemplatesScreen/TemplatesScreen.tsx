import { useTranslation } from "react-i18next";
import { EmptyState } from "@/components/feedback/EmptyState/EmptyState";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { ApplyTemplateDialog } from "@/components/templates/ApplyTemplateDialog/ApplyTemplateDialog";
import { SaveTemplateForm } from "@/components/templates/SaveTemplateForm/SaveTemplateForm";
import { TemplatesTable } from "@/components/templates/TemplatesTable/TemplatesTable";
import { useTemplatesScreen } from "./TemplatesScreen.hook";
import styles from "./TemplatesScreen.module.css";

/** SCR-23: reusable roughness, thresholds and facade defaults (never a location). */
export function TemplatesScreen() {
  const { t } = useTranslation();
  const s = useTemplatesScreen();
  return (
    <div className={styles.root}>
      <header className={styles.header}>
        <h1 className={styles.title}>{t("templates:title")}</h1>
        <p className={styles.lead}>{t("templates:lead")}</p>
      </header>
      {s.error ? <ErrorNotice error={s.error} /> : null}
      {s.empty ? <EmptyState title={t("templates:emptyTitle")} lead={t("templates:emptyLead")} /> : null}
      {s.templates.length > 0 ? <TemplatesTable templates={s.templates} onApply={s.onApply} onDelete={s.onDelete} /> : null}
      <div className={styles.section}>
        <SaveTemplateForm />
      </div>
      <ApplyTemplateDialog template={s.applying} onClose={s.onCloseApply} />
    </div>
  );
}
