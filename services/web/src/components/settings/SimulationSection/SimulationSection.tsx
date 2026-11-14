import { useTranslation } from "react-i18next";
import { FieldErrors } from "@/components/settings/FieldErrors/FieldErrors";
import type { SettingsDraft } from "@/components/settings/SettingsScreen/SettingsScreen.hook";
import { ParamField } from "@/components/forms/ParamField/ParamField";
import styles from "@/components/settings/SettingsScreen/SettingsScreen.module.css";

/** Turbulence, vegetation drag and the alternatives limit. */
export function SimulationSection({ form }: { form: SettingsDraft }) {
  const { t } = useTranslation();
  const d = form.draft;
  return (
    <section className={styles.section} aria-labelledby="settings-sim">
      <h2 id="settings-sim" className={styles.sectionTitle}>
        {t("settings:simulation.title")}
      </h2>
      <div className={styles.fields}>
        <ParamField id="ti" label={t("settings:simulation.ti")} percent value={d.turbulence_intensity_default} min={0} max={1} defaultValue={0.25} help={t("settings:simulation.tiHelp")} onCommit={(v) => form.set(["turbulence_intensity_default"], v)} />
        <FieldErrors errors={form.fieldErrors} path="turbulence_intensity_default" />
        <ParamField id="veg-cd" label={t("settings:simulation.cd")} value={d.vegetation_cd} min={0.05} max={1} decimals={2} defaultValue={0.2} help={t("settings:simulation.cdHelp")} onCommit={(v) => form.set(["vegetation_cd"], v)} />
        <FieldErrors errors={form.fieldErrors} path="vegetation_cd" />
        <ParamField id="alt-limit" label={t("settings:simulation.limit")} value={d.alternatives_limit} min={1} max={20} decimals={0} defaultValue={8} help={t("settings:simulation.limitHelp")} onCommit={(v) => form.set(["alternatives_limit"], Math.round(v))} />
        <FieldErrors errors={form.fieldErrors} path="alternatives_limit" />
      </div>
    </section>
  );
}
