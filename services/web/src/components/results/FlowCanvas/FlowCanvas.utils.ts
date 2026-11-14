import type { TFunction } from "i18next";
import { formatNumber, formatUnit } from "@/lib/format/format.number";

/** "K 1,34 — 5,1 m/s" under the cursor; null over buildings or outside. */
export function readoutText(k: number, speed: number | null, t: TFunction): string | null {
  if (!Number.isFinite(k)) return null;
  if (speed === null || !Number.isFinite(speed)) return `K ${formatNumber(k, 2)}`;
  return t("results:flow.readout", { k: formatNumber(k, 2), speed: formatUnit(speed, 1, "m/s") });
}

const NICE = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000];

/** Largest round scale-bar length that fits in ~100 px at the current pixels per metre. */
export function scaleBar(pxPerMetre: number, _zoom: number): { metres: number; px: number } {
  const target = 100 / pxPerMetre;
  const metres = NICE.filter((n) => n <= target * 1.001).pop() ?? NICE[0];
  return { metres, px: Math.round(metres * pxPerMetre) };
}
