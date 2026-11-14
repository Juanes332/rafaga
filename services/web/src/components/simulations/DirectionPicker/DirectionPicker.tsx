import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { WindRose } from "@/components/wind/WindRose/WindRose";
import type { WindSector } from "@/types/wind/wind.types";
import { useDirectionPicker } from "./DirectionPicker.hook";
import styles from "./DirectionPicker.module.css";

interface DirectionPickerProps {
  sectors: WindSector[] | null;
  disabled: boolean;
}

/** Clickable, keyboard-operable rose for choosing simulated directions. */
export function DirectionPicker({ sectors, disabled }: DirectionPickerProps) {
  const { t } = useTranslation();
  const d = useDirectionPicker(sectors);
  return (
    <section className={styles.root} aria-labelledby="directions-title">
      <div className={styles.head}>
        <h2 id="directions-title" className={styles.title}>
          {t("simulate:form.directions")}
        </h2>
        <p className={styles.help}>{t("simulate:form.directionsHelp")}</p>
      </div>
      <WindRose sectors={sectors} size={340} selected={d.selected} onToggle={disabled ? undefined : d.toggle} />
      <p className={styles.summary} aria-live="polite">
        <strong>{d.countText}</strong> {d.coverageText}
      </p>
      {!disabled ? (
        <div className={styles.actions}>
          {d.pickDominant ? (
            <Button size="sm" variant="secondary" onClick={d.pickDominant}>
              {t("simulate:form.selectDominant")}
            </Button>
          ) : null}
          <Button size="sm" variant="ghost" onClick={d.clear} disabled={d.selected.length === 0}>
            {t("simulate:form.clear")}
          </Button>
        </div>
      ) : null}
    </section>
  );
}
