/** Thin space (U+2009) between a number and its unit (design-system §8). */
export const THIN = " ";
const LOCALE = "es-CO";
const cache = new Map<number, Intl.NumberFormat>();

function formatter(decimals: number): Intl.NumberFormat {
  let f = cache.get(decimals);
  if (!f) {
    // es-CO omits grouping below 10 000 by default; the contract wants "1.020".
    f = new Intl.NumberFormat(LOCALE, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
      useGrouping: "always",
    });
    cache.set(decimals, f);
  }
  return f;
}

/** Format a number with fixed decimals; null/NaN → "—". */
export function formatNumber(value: number | null | undefined, decimals: number): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return formatter(decimals).format(value);
}

export function formatUnit(value: number | null | undefined, decimals: number, unit: string): string {
  const n = formatNumber(value, decimals);
  return n === "—" ? n : `${n}${THIN}${unit}`;
}

/** Fraction 0..1 → "6,1 %". */
export function formatPercent(fraction: number | null | undefined, decimals = 1): string {
  return formatUnit(fraction == null ? fraction : fraction * 100, decimals, "%");
}

/** Value already in percent units (API zone percent) → "6,1 %". */
export function formatPercentValue(percent: number | null | undefined, decimals = 1): string {
  return formatUnit(percent, decimals, "%");
}

export function formatArea(m2: number | null | undefined): string {
  return formatUnit(m2, 0, "m²");
}

export function formatCoord(value: number | null | undefined): string {
  return formatNumber(value, 5);
}

/** Parse user input that may use a decimal comma. */
export function parseLocaleNumber(text: string): number | null {
  const cleaned = text.trim().replace(/\s/g, "").replace(",", ".");
  if (cleaned === "" || cleaned === "-" || cleaned === ".") return null;
  const n = Number(cleaned);
  return Number.isFinite(n) ? n : null;
}
