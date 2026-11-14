import { useTranslation } from "react-i18next";
import { toDms } from "@/lib/format/format.coordinate";
import { formatCoord, formatUnit } from "@/lib/format/format.number";
import type { Project } from "@/types/projects/project.types";
import styles from "./LocationSummary.module.css";

/** Lat/lon (5 decimals and DMS), elevation and ISA density of the chosen site. */
export function LocationSummary({ project }: { project: Project }) {
  const { t } = useTranslation();
  const manual = project.elevation_source === "manual";
  const rows = [
    { label: t("location:summary.lat"), value: formatCoord(project.lat) },
    { label: t("location:summary.lon"), value: formatCoord(project.lon) },
    { label: t("location:summary.latDms"), value: toDms(project.lat, "lat") },
    { label: t("location:summary.lonDms"), value: toDms(project.lon, "lon") },
    { label: manual ? t("location:summary.elevationManual") : t("location:summary.elevation"), value: formatUnit(project.elevation_m, 0, "m") },
    { label: t("location:summary.density"), value: formatUnit(project.air_density_kg_m3, 3, "kg/m³") },
  ];
  return (
    <section className={styles.root} aria-labelledby="site-title">
      <h2 id="site-title" className={styles.title}>
        {t("location:summary.title")}
      </h2>
      <dl className={styles.list}>
        {rows.map((r) => (
          <div key={r.label} className={styles.row}>
            <dt>{r.label}</dt>
            <dd>{r.value}</dd>
          </div>
        ))}
      </dl>
      <p className={styles.note}>{t("location:summary.densityHelp")}</p>
    </section>
  );
}
