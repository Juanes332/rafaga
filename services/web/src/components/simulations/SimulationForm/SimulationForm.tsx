import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { ParamField } from "@/components/forms/ParamField/ParamField";
import { CpuWarningDialog } from "@/components/simulations/CpuWarningDialog/CpuWarningDialog";
import { EstimatePanel } from "@/components/simulations/EstimatePanel/EstimatePanel";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { SimDevice, SimKind } from "@/stores/simulations/simulations.store";
import { useSimulationForm } from "./SimulationForm.hook";
import type { SimulationFormProps } from "./SimulationForm.types";
import styles from "./SimulationForm.module.css";

const KINDS: SimKind[] = ["plan2d", "section2d", "volume3d"];
const DEVICES: SimDevice[] = ["auto", "cpu", "gpu"];

/** SCR-12 inspector: what, how fine and where to compute; estimate before launch. */
export function SimulationForm(props: SimulationFormProps) {
  const { t } = useTranslation();
  const s = useSimulationForm(props);
  return (
    <>
      <h2 className={styles.title}>{t("simulate:form.title")}</h2>
      <div className={styles.field}>
        <Label htmlFor="sim-alternative">{t("simulate:form.alternative")}</Label>
        <Select value={s.alternativeId ?? ""} onValueChange={s.f.setAlternative}>
          <SelectTrigger id="sim-alternative">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {props.alternatives.map((a) => (
              <SelectItem key={a.id} value={a.id}>
                {a.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <fieldset className={styles.fieldset}>
        <legend className={styles.legend}>{t("simulate:form.kind")}</legend>
        <RadioGroup value={s.f.kind} onValueChange={(v) => s.f.setKind(v as SimKind)}>
          {KINDS.map((k) => (
            <div key={k} className={styles.option}>
              <RadioGroupItem id={`kind-${k}`} value={k} aria-describedby={`kind-${k}-help`} />
              <div>
                <Label htmlFor={`kind-${k}`}>{t(`simulate:form.kinds.${k}`)}</Label>
                <p id={`kind-${k}-help`} className={styles.help}>
                  {t(`simulate:form.kindHelp.${k}`)}
                </p>
              </div>
            </div>
          ))}
        </RadioGroup>
      </fieldset>
      {s.section ? <p className={`reading ${styles.note}`}>{t("simulate:form.sectionNote")}</p> : null}
      <ParamField id="sim-dx" label={t("simulate:form.cellSize")} unit="m" min={0.25} max={20} decimals={2} defaultValue={1} value={s.f.dxM} help={t("simulate:form.cellSizeHelp")} onCommit={s.f.setDx} />
      <fieldset className={styles.fieldset}>
        <legend className={styles.legend}>{t("simulate:form.device")}</legend>
        <RadioGroup value={s.f.device} onValueChange={(v) => s.f.setDevice(v as SimDevice)} className={styles.inline}>
          {DEVICES.map((d) => (
            <div key={d} className={styles.option}>
              <RadioGroupItem id={`device-${d}`} value={d} />
              <Label htmlFor={`device-${d}`}>{t(`simulate:form.devices.${d}`)}</Label>
            </div>
          ))}
        </RadioGroup>
      </fieldset>
      <EstimatePanel estimate={s.estimate} loading={s.estimating} autoCoarsen={s.f.autoCoarsen} onUseProposed={s.f.setDx} onAutoCoarsen={s.f.setAutoCoarsen} />
      {s.estimateError ? <ErrorNotice error={s.estimateError} /> : null}
      {s.missingDirection ? <ErrorNotice message={t("simulate:form.needDirection")} /> : null}
      {s.launchError ? <ErrorNotice error={s.launchError} /> : null}
      <Button className={styles.submit} disabled={s.pending || s.section || s.solverOffline} aria-describedby={s.solverOffline ? "sim-offline-reason" : undefined} onClick={s.onLaunch}>
        {s.pending ? t("simulate:form.submitting") : t("simulate:form.submit")}
      </Button>
      {s.solverOffline ? (
        <p id="sim-offline-reason" className={styles.help}>
          {t("simulate:offlineReason")}
        </p>
      ) : null}
      <CpuWarningDialog open={s.confirmingCpu} nodes={s.estimate?.nodes ?? 0} etaSeconds={s.estimate?.eta_seconds ?? 0} onCancel={s.onCancelCpu} onConfirm={s.onConfirmCpu} />
    </>
  );
}
