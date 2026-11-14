import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { formatNumber, THIN } from "@/lib/format/format.number";
import type { ParamFieldProps } from "./ParamField.types";
import { checkInput, displayText, toDisplay } from "./ParamField.utils";

interface UseParamField {
  text: string;
  error: string | null;
  defaultText: string | null;
  rangeText: string | null;
  sliderValue: number[];
  onTextChange: (text: string) => void;
  onCommitText: () => void;
  onSliderChange: (v: number[]) => void;
  onSliderCommit: (v: number[]) => void;
}

/** Draft text with locale parsing; commits on blur/Enter and slider release. */
export function useParamField(p: ParamFieldProps): UseParamField {
  const { t } = useTranslation();
  const percent = p.percent ?? false;
  const decimals = p.decimals ?? 1;
  const [text, setText] = useState(displayText(p.value, decimals, percent));
  const [error, setError] = useState<string | null>(null);
  useEffect(() => setText(displayText(p.value, decimals, percent)), [p.value, decimals, percent]);

  const fmt = (v: number | null | undefined) => formatNumber(toDisplay(v ?? null, percent), percent ? 0 : decimals);
  const unit = p.unit ? `${THIN}${p.unit}` : "";

  const onCommitText = () => {
    const res = checkInput(text, p.min, p.max, percent);
    if (!res.ok) {
      setError(res.reason === "nan" ? t("common:field.notNumber") : t("common:field.outOfRange", { min: fmt(p.min), max: fmt(p.max) }));
      return;
    }
    setError(null);
    if (res.value !== p.value) p.onCommit(res.value);
  };

  return {
    text,
    error,
    defaultText: p.defaultValue != null ? t("common:default", { value: `${fmt(p.defaultValue)}${unit}` }) : null,
    rangeText: p.min != null && p.max != null ? t("common:range", { min: fmt(p.min), max: `${fmt(p.max)}${unit}` }) : null,
    sliderValue: [p.value ?? p.defaultValue ?? p.min ?? 0],
    onTextChange: (v) => setText(v),
    onCommitText,
    onSliderChange: ([v]) => setText(displayText(v, decimals, percent)),
    onSliderCommit: ([v]) => p.onCommit(v),
  };
}
