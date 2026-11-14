import { formatNumber, formatUnit } from "@/lib/format/format.number";

/** Bytes → "5,6 GB" (decimal GB, like the VRAM figures users know). */
export function formatBytes(bytes: number): string {
  return bytes >= 1e9 ? formatUnit(bytes / 1e9, 1, "GB") : formatUnit(bytes / 1e6, 0, "MB");
}

/** Cell size without trailing zeros: 1,5 m, 0,75 m, 2 m. */
export function formatDx(dx: number): string {
  const decimals = Number.isInteger(dx) ? 0 : Number.isInteger(dx * 10) ? 1 : 2;
  return formatUnit(dx, decimals, "m");
}

export function formatNodes(n: number): string {
  return n >= 1e6 ? `${formatNumber(n / 1e6, 1)} M` : formatNumber(n, 0);
}
