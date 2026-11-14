import { useTranslation } from "react-i18next";
import { formatArea, formatPercentValue } from "@/lib/format/format.number";
import { cn } from "@/lib/utils";
import type { ZoneLegendProps } from "./ZoneLegend.types";
import { ZoneSwatch } from "./ZoneSwatch";
import styles from "./ZoneLegend.module.css";

/** Pattern + colour + name + m² + % per zone. */
export function ZoneLegend({ items, className }: ZoneLegendProps) {
  const { t } = useTranslation();
  return (
    <section className={cn(styles.root, className)} aria-labelledby="zone-legend-title">
      <h2 id="zone-legend-title" className={styles.title}>
        {t("results:zone.title")}
      </h2>
      {items.length === 0 ? (
        <p className={styles.empty}>{t("results:zone.empty")}</p>
      ) : (
        <dl className={styles.list}>
          {items.map((z) => (
            <div key={z.zone} className={styles.row}>
              <dt className={styles.name}>
                <ZoneSwatch zone={z.zone} />
                <span className={z.zone === "acceleration" ? styles.accelText : undefined}>{t(`results:zone.${z.zone}`)}</span>
              </dt>
              <dd className={styles.num}>{formatArea(z.area_m2)}</dd>
              <dd className={styles.num}>{formatPercentValue(z.percent)}</dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  );
}
