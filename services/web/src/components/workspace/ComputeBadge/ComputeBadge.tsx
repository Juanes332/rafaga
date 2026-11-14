import { useTranslation } from "react-i18next";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { useComputeBadge } from "./ComputeBadge.hook";
import styles from "./ComputeBadge.module.css";

/** Compute device as plain text; the dot is filled when every service is healthy. */
export function ComputeBadge() {
  const { t } = useTranslation();
  const b = useComputeBadge();
  return (
    <Popover>
      <PopoverTrigger className={styles.trigger}>
        <span className={cn(styles.dot, b.healthy ? styles.ok : styles.down)} role="img" aria-label={b.healthLabel} />
        <span className={styles.label}>{b.label}</span>
      </PopoverTrigger>
      <PopoverContent align="end" className={styles.panel}>
        <h2 className={styles.title}>{t("common:compute.statusTitle")}</h2>
        <dl className={styles.list}>
          {b.services.map((s) => (
            <div key={s.key} className={styles.row}>
              <dt>{t(`common:compute.${s.key}`)}</dt>
              <dd className={s.ok ? undefined : styles.bad}>{s.ok ? t("common:compute.ok") : t("common:compute.down")}</dd>
            </div>
          ))}
        </dl>
        {b.cpuOnly ? <p className={styles.note}>{t("common:compute.gpuMissing")}</p> : null}
      </PopoverContent>
    </Popover>
  );
}
