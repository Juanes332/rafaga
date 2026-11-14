import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { LawsonSection } from "@/components/settings/LawsonSection/LawsonSection";
import { SimulationSection } from "@/components/settings/SimulationSection/SimulationSection";
import { ZoneThresholdsSection } from "@/components/settings/ZoneThresholdsSection/ZoneThresholdsSection";
import { Button } from "@/components/ui/button";
import { useSettingsScreen } from "./SettingsScreen.hook";
import styles from "./SettingsScreen.module.css";

/** SCR-21: thresholds, Lawson table and simulation defaults. */
export function SettingsScreen() {
  const { t } = useTranslation();
  const s = useSettingsScreen();
  return (
    <div className={styles.root}>
      <header className={styles.header}>
        <h1 className={styles.title}>{t("settings:title")}</h1>
        <p className={styles.lead}>{t("settings:lead")}</p>
      </header>
      {s.loadError ? <ErrorNotice error={s.loadError} /> : null}
      {s.loading ? <p className={styles.note}>{t("common:loading")}</p> : null}
      {s.form ? (
        <>
          <ZoneThresholdsSection form={s.form} />
          <LawsonSection form={s.form} />
          <SimulationSection form={s.form} />
        </>
      ) : null}
      {s.saveError ? <ErrorNotice error={s.saveError} /> : null}
      {s.form ? (
        <div className={styles.actions}>
          <Button onClick={s.onSave} disabled={!s.canSave}>
            {s.saving ? t("settings:saving") : t("settings:save")}
          </Button>
          {s.dirty ? (
            <Button variant="ghost" onClick={s.onReset}>
              {t("settings:reset")}
            </Button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
