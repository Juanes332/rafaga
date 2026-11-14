import { formatNumber, parseLocaleNumber } from "@/lib/format/format.number";

/** Display scale: percent fields show 0..1 values as 0..100. */
export function toDisplay(value: number | null, percent: boolean): number | null {
  return value === null ? null : percent ? value * 100 : value;
}

export function fromDisplay(value: number, percent: boolean): number {
  return percent ? value / 100 : value;
}

export function displayText(value: number | null, decimals: number, percent: boolean): string {
  const v = toDisplay(value, percent);
  return v === null ? "" : formatNumber(v, percent ? 0 : decimals).replace(/\./g, "");
}

export type FieldCheck = { ok: true; value: number } | { ok: false; reason: "nan" | "range" };

/** Parse a typed value and check it against the (display-scaled) range. */
export function checkInput(text: string, min: number | undefined, max: number | undefined, percent: boolean): FieldCheck {
  const parsed = parseLocaleNumber(text);
  if (parsed === null) return { ok: false, reason: "nan" };
  const lo = toDisplay(min ?? null, percent);
  const hi = toDisplay(max ?? null, percent);
  if ((lo !== null && parsed < lo - 1e-9) || (hi !== null && parsed > hi + 1e-9)) return { ok: false, reason: "range" };
  return { ok: true, value: fromDisplay(parsed, percent) };
}
