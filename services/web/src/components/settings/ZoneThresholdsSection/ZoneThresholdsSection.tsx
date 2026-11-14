import { useTranslation } from "react-i18next";
import { FieldErrors } from "@/components/settings/FieldErrors/FieldErrors";
import type { SettingsDraft } from "@/components/settings/SettingsScreen/SettingsScreen.hook";
import { ParamField } from "@/components/forms/ParamField/ParamField";
import { formatNumber } from "@/lib/format/format.number";
import styles from "@/components/settings/SettingsScreen/SettingsScreen.module.css";

/** K acceleration / stagnation and ΔK reduction thresholds. */
export function ZoneThresholdsSection({ form }: { form: SettingsDraft }) {
  const { t } = useTranslation();
  const th = form.draft.thresholds;
  return (
    <section className={styles.section} aria-labelledby="settings-zones">
      <h2 id="settings-zones" className={styles.sectionTitle}>
        {t("settings:zones.title")}
      </h2>
      <div className={styles.fields}>
        <ParamField id="k-accel" label={t("settings:zones.kAccel")} value={th.k_accel} min={1} max={2} step={0.05} decimals={2} defaultValue={1.2} help={t("settings:zones.kAccelHelp")} onCommit={(v) => form.set(["thresholds", "k_accel"], v)} />
        <FieldErrors errors={form.fieldErrors} path="thresholds.k_accel" />
        <ParamField id="k-stagnation" label={t("settings:zones.kStagnation")} value={th.k_stagnation} min={0.05} max={1} step={0.05} decimals={2} defaultValue={0.3} help={t("settings:zones.kStagnationHelp")} onCommit={(v) => form.set(["thresholds", "k_stagnation"], v)} />
        <FieldErrors errors={form.fieldErrors} path="thresholds.k_stagnation" />
        <ParamField id="dk-reduction" label={t("settings:zones.dkReduction")} value={th.dk_reduction} min={-0.6} max={0} step={0.05} decimals={2} defaultValue={-0.1} help={t("settings:zones.dkReductionHelp")} onCommit={(v) => form.set(["thresholds", "dk_reduction"], v)} />
        <FieldErrors errors={form.fieldErrors} path="thresholds.dk_reduction" />
      </div>
      {form.order.zones ? <p className={styles.error}>{t("settings:zones.orderError")}</p> : null}
      <div className={styles.notes}>
        <p className="reading">{t("glossary:acceleration", { value: formatNumber(th.k_accel, 2) })}</p>
        <p className="reading">{t("glossary:stagnation", { value: formatNumber(th.k_stagnation, 2) })}</p>
        <p className="reading">{t("glossary:reduction", { value: formatNumber(Math.abs(th.dk_reduction), 2) })}</p>
      </div>
    </section>
  );
}
