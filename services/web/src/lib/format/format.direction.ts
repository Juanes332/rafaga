export const DIRECTION_NAMES = [
  "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
  "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO",
] as const;

/** Index 0..15 of the 22.5° sector containing a meteorological "from" bearing. */
export function sectorIndex(deg: number): number {
  const norm = ((deg % 360) + 360) % 360;
  return Math.round(norm / 22.5) % 16;
}

/** Spanish compass name of a bearing at 4, 8 or 16 points of resolution. */
export function degToCardinal(deg: number, points: 4 | 8 | 16 = 16): string {
  if (!Number.isFinite(deg)) return "—";
  const step = 16 / points;
  const norm = ((deg % 360) + 360) % 360;
  const i = Math.round(norm / (360 / points)) % points;
  return DIRECTION_NAMES[i * step];
}

export function directionName(deg: number): string {
  return degToCardinal(deg, 16);
}

/** "desde NE · 45°": meteorological convention, the bearing the wind comes FROM. */
export function windFromLabel(deg: number): string {
  // Wrap after rounding so 359.96 reads 0° and -45 reads 315°, matching the name.
  const rounded = (((Math.round(deg * 10) / 10) % 360) + 360) % 360;
  return `desde ${directionName(deg)} · ${String(rounded).replace(".", ",")}°`;
}

/** Every wind direction shown in the UI goes through this label. */
export const directionLabel = windFromLabel;

/** The 16 sector centres in degrees. */
export const SECTOR_CENTRES: number[] = Array.from({ length: 16 }, (_, i) => i * 22.5);
