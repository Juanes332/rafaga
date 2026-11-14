import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { Button } from "@/components/ui/button";
import { LAWSON_COLORS } from "@/engines/colormaps/colormap";
import { formatArea, formatPercent, formatPercentValue } from "@/lib/format/format.number";
import { cn } from "@/lib/utils";
import { useLawsonPanel } from "./LawsonPanel.hook";
import styles from "./LawsonPanel.module.css";

interface LawsonPanelProps {
  studyId: string;
  readOnly: boolean;
}

/** Lawson classes with coverage, Parcial badge, areas and a plain-language note per class. */
export function LawsonPanel({ studyId, readOnly }: LawsonPanelProps) {
  const { t } = useTranslation();
  const l = useLawsonPanel(studyId);
  if (l.error) return <ErrorNotice error={l.error} />;
  if (!l.comfort) return null;
  const rows = [...(l.comfort.class_areas ?? []), ...(l.comfort.safety_areas ?? [])].map((r) => ({ ...r, class: String(r.class ?? "") }));
  return (
    <section className={styles.root} aria-labelledby="lawson-title">
      <div className={styles.head}>
        <h2 id="lawson-title" className={styles.title}>
          {t("results:lawson.title")}
        </h2>
        {l.comfort.partial ? <span className={styles.badge}>{t("results:lawson.partial")}</span> : null}
      </div>
      <p className={styles.meta}>{t("results:lawson.coverage", { value: formatPercent(l.comfort.coverage) })}</p>
      {l.comfort.partial ? <p className={styles.meta}>{t("results:lawson.partialHelp")}</p> : null}
      {l.comfort.status === "failed" ? <ErrorNotice message={t("results:lawson.failed")} /> : null}
      <ul className={styles.list} aria-label={t("results:lawson.selectClass")}>
        {rows.map((r, i) => (
          <li key={r.class}>
            <button
              type="button"
              className={cn(styles.row, l.selected === r.class && styles.selected)}
              aria-pressed={l.selected === r.class}
              onClick={() => l.select(r.class)}
            >
              <span
                className={r.class.startsWith("S") ? styles.safety : styles.swatch}
                style={r.class.startsWith("S") ? undefined : { background: `rgb(${LAWSON_COLORS[i].join(" ")})` }}
                aria-hidden
              />
              <span className={styles.name}>{t(`results:lawson.classes.${r.class}`, { defaultValue: r.class })}</span>
              <span className={styles.num}>{formatArea(r.area_m2)}</span>
              <span className={styles.num}>{formatPercentValue(r.percent)}</span>
            </button>
          </li>
        ))}
      </ul>
      {l.selected ? <p className="reading">{t(`results:lawson.notes.${l.selected}`, { defaultValue: "" })}</p> : null}
      {readOnly ? null : (
        <div className={styles.recompute}>
          <p className={styles.meta}>{t("results:lawson.recomputeHelp")}</p>
          <Button variant="outline" size="sm" disabled={l.recomputing} onClick={l.recompute}>
            {l.recomputing ? t("results:lawson.recomputing") : t("results:lawson.recompute")}
          </Button>
          {l.recomputeError ? <ErrorNotice error={l.recomputeError} /> : null}
        </div>
      )}
    </section>
  );
}
