import { cn } from "@/lib/utils";
import { useKLegend } from "./KLegend.hook";
import type { KLegendProps } from "./KLegend.types";
import styles from "./KLegend.module.css";

/** Numeric colour legend with units; never auto-scaled. */
export function KLegend(props: KLegendProps) {
  const l = useKLegend(props);
  return (
    <figure className={cn(styles.root, props.className)} aria-label={l.title}>
      <figcaption className={styles.title}>{l.title}</figcaption>
      <div className={styles.barRow}>
        {l.bothEnds ? <span className={styles.arrowLeft} aria-hidden /> : null}
        <div className={styles.bar} style={{ background: l.gradient }}>
          {l.marks.map((m) => (
            <span key={m.value} className={styles.mark} style={{ left: `${m.at}%` }} title={m.label} />
          ))}
        </div>
        <span className={styles.arrow} role="img" aria-label={l.saturationLabel} title={l.saturationLabel} />
      </div>
      <div className={styles.ticks}>
        {l.ticks.map((tk) => (
          <span key={tk.value} className={styles.tick} style={{ left: `${tk.at}%` }}>
            {tk.label}
          </span>
        ))}
      </div>
    </figure>
  );
}
