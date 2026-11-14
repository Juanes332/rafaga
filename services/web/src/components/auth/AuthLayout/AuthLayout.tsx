import { useMemo, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { cylinderStreamlines } from "@/engines/flow/cylinder-flow";
import styles from "./AuthLayout.module.css";

/** The only centred screen: 360 px column over faint static streamlines (no motion). */
export function AuthLayout({ children }: { children: ReactNode }) {
  const { t } = useTranslation();
  const paths = useMemo(() => cylinderStreamlines({ width: 1600, height: 1000, lines: 26, radius: 0.09 }), []);
  return (
    <div className={styles.root}>
      <svg className={styles.bg} viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMid slice" aria-hidden>
        {paths.map((d, i) => (
          <path key={i} d={d} />
        ))}
      </svg>
      <main id="main" className={styles.column}>
        <p className={styles.brand}>{t("common:appName")}</p>
        {children}
      </main>
    </div>
  );
}
