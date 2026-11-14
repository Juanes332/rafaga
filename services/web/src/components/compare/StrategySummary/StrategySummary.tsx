import { ArrowDownRight, ArrowUpRight, Equal } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useStrategySummary } from "./StrategySummary.hook";
import type { StrategySummaryProps } from "./StrategySummary.types";
import styles from "./StrategySummary.module.css";

const ICON = { improves: ArrowDownRight, worsens: ArrowUpRight, neutral: Equal } as const;

/** BL-12: what the strategy does to the wind, in plain Spanish, with a verdict that is never colour-only. */
export function StrategySummary(p: StrategySummaryProps) {
  const { t } = useTranslation();
  const { summary, lines, details } = useStrategySummary(p);
  const Icon = ICON[summary.verdict];
  const sentences = lines.slice(0, -1);
  return (
    <section className={styles.root} aria-labelledby="strategy-summary-title" data-verdict={summary.verdict}>
      <div className={styles.head}>
        <h2 id="strategy-summary-title" className={styles.title}>
          {t("compare:summary.title", { name: summary.name, base: summary.baseName })}
        </h2>
        <span className={styles.verdict} data-verdict={summary.verdict}>
          <Icon aria-hidden size={16} />
          {t(`compare:summary.verdictLabel.${summary.verdict}`)}
        </span>
      </div>
      <ul className={styles.list}>
        {sentences.map((s) => (
          <li key={s}>{s}</li>
        ))}
        <li className={styles.final}>{lines[lines.length - 1]}</li>
      </ul>
      {p.comfortMissing ? <p className={styles.note}>{t("compare:summary.comfortMissing")}</p> : null}
      <details className={styles.details}>
        <summary>{t("compare:summary.details")}</summary>
        {details.map((d) => (
          <p key={d}>{d}</p>
        ))}
      </details>
    </section>
  );
}
