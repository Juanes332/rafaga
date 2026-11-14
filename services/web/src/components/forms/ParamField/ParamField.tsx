import { Info } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useParamField } from "./ParamField.hook";
import type { ParamFieldProps } from "./ParamField.types";
import styles from "./ParamField.module.css";

/** Numeric parameter: value + unit, default, range and help; shows API adjustments. */
export function ParamField(props: ParamFieldProps) {
  const { t } = useTranslation();
  const f = useParamField(props);
  const hintId = `${props.id}-hint`;
  return (
    <div className={styles.root}>
      <div className={styles.labelRow}>
        <Label htmlFor={props.id}>{props.label}</Label>
        {props.help ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <button type="button" className={styles.help} aria-label={t("common:field.helpFor", { label: props.label })}>
                <Info aria-hidden size={15} />
              </button>
            </TooltipTrigger>
            <TooltipContent side="left">{props.help}</TooltipContent>
          </Tooltip>
        ) : null}
      </div>
      {props.slider && props.min != null && props.max != null ? (
        <Slider
          min={props.min}
          max={props.max}
          step={props.step ?? (props.max - props.min) / 100}
          value={f.sliderValue}
          disabled={props.disabled}
          thumbLabel={props.label}
          onValueChange={f.onSliderChange}
          onValueCommit={f.onSliderCommit}
        />
      ) : null}
      <div className={styles.inputRow}>
        <Input
          id={props.id}
          inputMode="decimal"
          value={f.text}
          disabled={props.disabled}
          aria-invalid={f.error ? true : undefined}
          aria-describedby={hintId}
          className={styles.input}
          onChange={(e) => f.onTextChange(e.target.value)}
          onBlur={f.onCommitText}
          onKeyDown={(e) => e.key === "Enter" && f.onCommitText()}
        />
        {props.unit || props.percent ? <span className={styles.unit}>{props.percent ? "%" : props.unit}</span> : null}
      </div>
      <p id={hintId} className={styles.hint}>
        {[f.defaultText, f.rangeText].filter(Boolean).join(". ")}
      </p>
      {f.error ? <p className={styles.error}>{f.error}</p> : null}
      {props.adjustment ? <p className={styles.adjusted} role="status">{props.adjustment}</p> : null}
    </div>
  );
}
