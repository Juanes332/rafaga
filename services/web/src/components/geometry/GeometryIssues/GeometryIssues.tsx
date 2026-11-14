import { useTranslation } from "react-i18next";
import type { GeometryIssue } from "@/types/geometry/geometry.types";
import { useGeometryIssues } from "./GeometryIssues.hook";
import styles from "./GeometryIssues.module.css";

/** Issues list: client self-intersection checks plus /geometry/validate results. */
export function GeometryIssues({ serverIssues }: { serverIssues: GeometryIssue[] }) {
  const { t } = useTranslation();
  const { rows, onSelect } = useGeometryIssues(serverIssues);
  return (
    <section className={styles.root} aria-labelledby="issues-title">
      <h2 id="issues-title" className={styles.title}>
        {t("geometry:issues.title")}
      </h2>
      {rows.length === 0 ? <p className={styles.none}>{t("geometry:issues.none")}</p> : null}
      <ul className={styles.list}>
        {rows.map((r) => (
          <li key={r.key} className={styles.item}>
            {r.buildingName ? <strong className={styles.name}>{r.buildingName}</strong> : null}
            <span>{r.text}</span>
            {r.buildingId ? (
              <button type="button" className={styles.link} onClick={() => onSelect(r.buildingId as string)}>
                {t("geometry:issues.select")}
              </button>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}
