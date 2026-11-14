import { Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { AccountMenu } from "@/components/workspace/AccountMenu/AccountMenu";
import { ComputeBadge } from "@/components/workspace/ComputeBadge/ComputeBadge";
import { ThemeToggle } from "@/components/workspace/ThemeToggle/ThemeToggle";
import type { TopBarProps } from "./TopBar.types";
import styles from "./TopBar.module.css";

/** 44 px bar: wordmark, breadcrumb, compute badge, theme and account. Regions separated by space. */
export function TopBar({ projectName }: TopBarProps) {
  const { t } = useTranslation();
  return (
    <header className={styles.root}>
      <a href="#main" className={styles.skip}>
        {t("common:nav.skip")}
      </a>
      <Link to="/projects" className={styles.brand}>
        {t("common:appName")}
      </Link>
      <nav aria-label={t("common:nav.breadcrumb")} className={styles.crumbs}>
        <Link to="/projects" className={styles.crumb}>
          {t("common:nav.projects")}
        </Link>
        {projectName ? (
          <>
            <span aria-hidden className={styles.sep}>
              /
            </span>
            <span className={styles.current} aria-current="page">
              {projectName}
            </span>
          </>
        ) : null}
      </nav>
      <div className={styles.tools}>
        <ComputeBadge />
        <ThemeToggle />
        <AccountMenu />
      </div>
    </header>
  );
}
