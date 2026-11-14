import { useTranslation } from "react-i18next";
import { FieldErrors } from "@/components/settings/FieldErrors/FieldErrors";
import type { SettingsDraft } from "@/components/settings/SettingsScreen/SettingsScreen.hook";
import { ParamField } from "@/components/forms/ParamField/ParamField";
import styles from "@/components/settings/SettingsScreen/SettingsScreen.module.css";

// Labels follow the LDDC class order, so the API's label_key spelling never leaks into the UI.
const COMFORT = ["sitting", "standing", "strolling", "business", "uncomfortable"];
const SAFETY = ["safety15", "safety20"];

/** Lawson LDDC table: exceedance probabilities and one threshold per activity. */
export function LawsonSection({ form }: { form: SettingsDraft }) {
  const { t } = useTranslation();
  const l = form.draft.lawson;
  return (
    <section className={styles.section} aria-labelledby="settings-lawson">
      <h2 id="settings-lawson" className={styles.sectionTitle}>
        {t("settings:lawson.title")}
      </h2>
      <p className="reading">{t("glossary:lawson")}</p>
      <div className={styles.fields}>
        <ParamField id="lawson-exceedance" label={t("settings:lawson.exceedance")} unit="%" value={l.exceedance_probability * 100} min={0.5} max={20} decimals={1} defaultValue={5} help={t("settings:lawson.exceedanceHelp")} onCommit={(v) => form.set(["lawson", "exceedance_probability"], v / 100)} />
      </div>
      <h3 className={styles.subTitle}>{t("settings:lawson.classes")}</h3>
      <div className={styles.grid}>
        {l.comfort.map((c, i) =>
          c.threshold_ms === null ? null : (
            <div key={c.key}>
              <ParamField id={`lawson-${c.key}`} label={t(`settings:lawson.${COMFORT[i] ?? "uncomfortable"}`)} unit="m/s" value={c.threshold_ms} min={1} max={30} decimals={1} onCommit={(v) => form.set(["lawson", "comfort", i, "threshold_ms"], v)} />
              <FieldErrors errors={form.fieldErrors} path={`lawson.comfort.${i}.threshold_ms`} />
            </div>
          ),
        )}
      </div>
      <p className={styles.note}>{t("settings:lawson.uncomfortableNote")}</p>
      <h3 className={styles.subTitle}>{t("settings:lawson.safety")}</h3>
      <div className={styles.grid}>
        <ParamField id="lawson-safety-p" label={t("settings:lawson.safetyProbability")} unit="%" value={l.safety_probability * 100} min={0.001} max={1} decimals={3} defaultValue={0.025} help={t("settings:lawson.safetyProbabilityHelp")} onCommit={(v) => form.set(["lawson", "safety_probability"], v / 100)} />
        {l.safety.map((s, i) => (
          <ParamField key={s.key} id={`lawson-${s.key}`} label={t(`settings:lawson.${SAFETY[i] ?? "safety20"}`)} unit="m/s" value={s.threshold_ms} min={5} max={40} decimals={1} onCommit={(v) => form.set(["lawson", "safety", i, "threshold_ms"], v)} />
        ))}
      </div>
      {form.order.lawson ? <p className={styles.error}>{t("settings:lawson.orderError")}</p> : null}
    </section>
  );
}
