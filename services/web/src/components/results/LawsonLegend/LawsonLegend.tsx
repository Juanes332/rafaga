import { useTranslation } from "react-i18next";
import { LAWSON_COLORS } from "@/engines/colormaps/colormap";
import styles from "./LawsonLegend.module.css";

const CLASSES = ["A", "B", "C", "D", "E"] as const;

/** Five Lawson classes sampled from cmocean speed, always with their names. */
export function LawsonLegend() {
  const { t } = useTranslation();
  return (
    <figure className={styles.root} aria-label={t("results:lawson.title")}>
      <figcaption className={styles.title}>{t("results:lawson.title")}</figcaption>
      <ul className={styles.list}>
        {CLASSES.map((c, i) => (
          <li key={c} className={styles.item}>
            <span className={styles.swatch} style={{ background: `rgb(${LAWSON_COLORS[i].join(" ")})` }} aria-hidden />
            {t(`results:lawson.classes.${c}`)}
          </li>
        ))}
      </ul>
    </figure>
  );
}
