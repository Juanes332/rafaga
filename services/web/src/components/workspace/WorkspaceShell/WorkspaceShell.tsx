import { Link, Outlet } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { StepRail } from "@/components/workspace/StepRail/StepRail";
import { TopBar } from "@/components/workspace/TopBar/TopBar";
import { useWorkspaceShell } from "./WorkspaceShell.hook";
import styles from "./WorkspaceShell.module.css";

/** Rail on the left, the step (canvas + inspector) on the right, thin bar on top. */
export function WorkspaceShell() {
  const { t } = useTranslation();
  const s = useWorkspaceShell();
  if (s.error) {
    return (
      <div className={styles.root}>
        <TopBar />
        <main id="main" className={styles.errorMain}>
          <ErrorNotice error={s.error} />
          <Link to="/projects">{t("common:goProjects")}</Link>
        </main>
      </div>
    );
  }
  return (
    <div className={styles.root}>
      <TopBar projectName={s.projectName} />
      {s.readOnly ? <p className={styles.readOnly}>{t("common:readOnly")}</p> : null}
      <div className={styles.body}>
        <StepRail projectId={s.projectId} />
        <main id="main" className={styles.main}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
