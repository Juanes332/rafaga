import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { CreateUserForm } from "@/components/users/CreateUserForm/CreateUserForm";
import { DeleteUserDialog } from "@/components/users/DeleteUserDialog/DeleteUserDialog";
import { ProjectSharesPanel } from "@/components/users/ProjectSharesPanel/ProjectSharesPanel";
import { UsersTable } from "@/components/users/UsersTable/UsersTable";
import { useUsersScreen } from "./UsersScreen.hook";
import styles from "./UsersScreen.module.css";

/** SCR-22: accounts and per-project access. */
export function UsersScreen() {
  const { t } = useTranslation();
  const s = useUsersScreen();
  return (
    <div className={styles.root}>
      <header className={styles.header}>
        <h1 className={styles.title}>{t("users:title")}</h1>
        <p className={styles.lead}>{s.isArchitect ? t("users:lead") : t("users:reviewerOnly")}</p>
      </header>
      {s.isArchitect ? (
        <>
          <section className={styles.section} aria-labelledby="users-list">
            <h2 id="users-list" className={styles.sectionTitle}>
              {t("users:list")}
            </h2>
            {s.loadError ? <ErrorNotice error={s.loadError} /> : null}
            {s.deleteError ? <ErrorNotice error={s.deleteError} /> : null}
            <UsersTable users={s.users} selfId={s.selfId} onDelete={s.onDelete} />
          </section>
          <div className={styles.section}>
            <CreateUserForm />
          </div>
          <div className={styles.section}>
            <ProjectSharesPanel selfId={s.selfId} />
          </div>
          <DeleteUserDialog email={s.deleting?.email ?? null} onCancel={s.onCancelDelete} onConfirm={s.onConfirmDelete} />
        </>
      ) : null}
    </div>
  );
}
