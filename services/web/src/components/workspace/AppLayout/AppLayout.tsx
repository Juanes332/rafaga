import { Outlet } from "@tanstack/react-router";
import { TopBar } from "@/components/workspace/TopBar/TopBar";
import styles from "./AppLayout.module.css";

/** Pages outside a project: top bar + a single readable column. */
export function AppLayout() {
  return (
    <div className={styles.root}>
      <TopBar />
      <main id="main" className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}
