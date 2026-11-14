import { Plus } from "lucide-react";
import { useTranslation } from "react-i18next";
import { EmptyState } from "@/components/feedback/EmptyState/EmptyState";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { DeleteProjectDialog } from "@/components/projects/DeleteProjectDialog/DeleteProjectDialog";
import { ProjectNameDialog } from "@/components/projects/ProjectNameDialog/ProjectNameDialog";
import { ProjectsTable } from "@/components/projects/ProjectsTable/ProjectsTable";
import { Button } from "@/components/ui/button";
import { useProjectsScreen } from "./ProjectsScreen.hook";
import styles from "./ProjectsScreen.module.css";

/** SCR-03: project list with create, rename, duplicate and delete. */
export function ProjectsScreen() {
  const { t } = useTranslation();
  const s = useProjectsScreen();
  const empty = !s.isLoading && !s.error && s.projects.length === 0;
  return (
    <div className={styles.root}>
      <header className={styles.header}>
        <h1 className={styles.title}>{t("projects:title")}</h1>
        {!empty ? (
          <Button onClick={() => s.setCreating(true)}>
            <Plus aria-hidden />
            {t("projects:new")}
          </Button>
        ) : null}
      </header>
      {s.error ? <ErrorNotice error={s.error} actionLabel={t("common:retry")} onAction={s.retry} /> : null}
      {s.isLoading ? <p className={styles.loading}>{t("common:loading")}</p> : null}
      {empty ? (
        <EmptyState title={t("projects:emptyTitle")} lead={t("projects:emptyLead")}>
          <Button onClick={() => s.setCreating(true)}>{t("projects:new")}</Button>
        </EmptyState>
      ) : null}
      {s.projects.length > 0 ? (
        <ProjectsTable projects={s.projects} onRename={s.setRenaming} onDuplicate={s.onDuplicate} onDelete={s.setDeleting} />
      ) : null}
      <ProjectNameDialog
        open={s.creating}
        title={t("projects:create.title")}
        submitLabel={t("projects:create.submit")}
        pending={s.create.isPending}
        error={s.create.error}
        onOpenChange={s.setCreating}
        onSubmit={s.onCreate}
      />
      <ProjectNameDialog
        open={s.renaming !== null}
        title={t("projects:renameDialog.title")}
        submitLabel={t("projects:renameDialog.submit")}
        initialName={s.renaming?.name}
        pending={s.update.isPending}
        error={s.update.error}
        onOpenChange={(o) => !o && s.setRenaming(null)}
        onSubmit={s.onRenameSubmit}
      />
      <DeleteProjectDialog name={s.deleting?.name ?? null} onCancel={() => s.setDeleting(null)} onConfirm={s.onConfirmDelete} />
    </div>
  );
}
