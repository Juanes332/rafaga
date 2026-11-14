import type { TFunction } from "i18next";
import { formatNumber } from "@/lib/format/format.number";
import type { Adjustment, FacadeStrategy } from "@/types/facades/facade.types";
import type { ParamView } from "./FacadeEditor.types";

/** Catalogue defaults for a strategy (null defaults stay null: the api fills them). */
export function defaultParams(strategy: FacadeStrategy | undefined): Record<string, number | null> {
  return Object.fromEntries((strategy?.parameters ?? []).map((p) => [p.key, p.default]));
}

export function paramViews(strategy: FacadeStrategy | undefined, values: Record<string, number | null>, t: TFunction): ParamView[] {
  return (strategy?.parameters ?? []).map((p) => ({
    key: p.key,
    label: t(`alternatives:params.${p.key}`, { defaultValue: p.key }),
    help: t(`alternatives:paramHelp.${p.key}`, { defaultValue: "" }),
    unit: p.unit,
    min: p.min,
    max: p.max,
    defaultValue: p.default,
    value: values[p.key] ?? null,
    percent: p.key === "porosity",
    decimals: p.key === "start_floor" ? 0 : 2,
  }));
}

/** "Se ajustó Altura de 40 m a 36 m: …" for each clamped value. */
export function adjustmentMessages(adjustments: Adjustment[], t: TFunction): string[] {
  return adjustments.map((a) => {
    const field = t(`alternatives:params.${a.field}`, { defaultValue: a.field });
    const values = { field, requested: formatNumber(a.requested, 1), applied: formatNumber(a.applied, 1) };
    return a.reason?.includes("building") ? t("alternatives:editor.adjusted", values) : t("alternatives:editor.adjustedGeneric", values);
  });
}
