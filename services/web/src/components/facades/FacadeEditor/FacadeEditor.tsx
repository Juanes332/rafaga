import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { ParamField } from "@/components/forms/ParamField/ParamField";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { StrategyType } from "@/types/facades/facade.types";
import { useFacadeEditor } from "./FacadeEditor.hook";
import type { FacadeEditorProps } from "./FacadeEditor.types";
import styles from "./FacadeEditor.module.css";

/** Strategy + parameters for the selected façade edge, with defaults, ranges and help. */
export function FacadeEditor(props: FacadeEditorProps) {
  const { t } = useTranslation();
  const e = useFacadeEditor(props);
  const existing = props.element !== null;
  return (
    <section className={styles.root} aria-labelledby="facade-editor-title">
      <h2 id="facade-editor-title" className={styles.title}>
        {t("alternatives:editor.selected", { index: props.edge.edgeIndex + 1, building: props.buildingName })}
      </h2>
      <div className={styles.field}>
        <Label htmlFor="strategy">{t("alternatives:editor.strategy")}</Label>
        <Select value={e.type} onValueChange={(v) => e.setType(v as StrategyType)} disabled={existing || props.readOnly}>
          <SelectTrigger id="strategy">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {e.strategies.map((s) => (
              <SelectItem key={s.type} value={s.type}>
                {t(`alternatives:strategies.${s.type}`)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className={`reading ${styles.help}`}>{t(`alternatives:strategyHelp.${e.type}`)}</p>
      </div>
      {e.params.map((p) => (
        <ParamField
          key={`${e.type}-${p.key}`}
          id={`param-${p.key}`}
          label={p.label}
          help={p.help}
          unit={p.unit || undefined}
          min={p.min}
          max={p.max}
          defaultValue={p.defaultValue}
          value={p.value}
          percent={p.percent}
          decimals={p.decimals}
          slider={p.percent}
          disabled={props.readOnly}
          onCommit={(v) => e.onParam(p.key, v)}
        />
      ))}
      {e.adjustments.map((m) => (
        <p key={m} role="status" className={styles.adjusted}>
          {m}
        </p>
      ))}
      {e.error ? <ErrorNotice error={e.error} /> : null}
      {!props.readOnly ? (
        <div className={styles.actions}>
          {existing ? (
            <Button variant="outline" disabled={e.pending} onClick={e.onRemove}>
              {t("alternatives:editor.remove")}
            </Button>
          ) : (
            <Button disabled={e.pending} onClick={e.onApply}>
              {e.pending ? t("alternatives:editor.applying") : t("alternatives:editor.apply")}
            </Button>
          )}
        </div>
      ) : null}
    </section>
  );
}
