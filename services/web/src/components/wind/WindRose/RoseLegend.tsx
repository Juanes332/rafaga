import { useTranslation } from "react-i18next";
import { lutGradient, SPEED_LUT } from "@/engines/colormaps/colormap";
import { formatNumber } from "@/lib/format/format.number";
import { ROSE_SPEED_MAX } from "./WindRose.utils";
import styles from "./WindRose.module.css";

const TICKS = [0, 3, 6, 9, 12];

/** Numeric legend for petal colour (typical speed, m/s) and the calm share. */
export function RoseLegend({ calm }: { calm: string }) {
  const { t } = useTranslation();
  // Petals use the whole speed LUT over a fixed 0–12 m/s domain.
  return (
    <figure className={styles.legend}>
      <figcaption className={styles.legendTitle}>{`${t("wind:rose.legend")}, m/s`}</figcaption>
      <div className={styles.bar} style={{ background: lutGradient(SPEED_LUT) }} aria-hidden />
      <div className={styles.ticks} aria-hidden>
        {TICKS.map((v) => (
          <span key={v} style={{ left: `${(v / ROSE_SPEED_MAX) * 100}%` }}>
            {formatNumber(v, 0)}
          </span>
        ))}
      </div>
      <p className={styles.calm}>{t("wind:rose.calm", { value: calm })}</p>
    </figure>
  );
}
