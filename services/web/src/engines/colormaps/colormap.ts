import { BALANCE_HEX, SPEED_HEX } from "./cmocean.lut";

function decode(hex: string): Uint8Array {
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i += 1) out[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  return out;
}

/** 256×RGB lookup tables (WEB-04), flat Uint8Array [r0,g0,b0,r1,…]. */
export const SPEED_LUT = decode(SPEED_HEX);
export const BALANCE_LUT = decode(BALANCE_HEX);

/** Fixed data domains (design-system §2.5): never auto-scaled, so colour means the same everywhere. */
export const K_DOMAIN: readonly [number, number] = [0, 2];
export const DK_DOMAIN: readonly [number, number] = [-0.6, 0.6];
export const K_TICKS = [0, 0.3, 0.6, 1, 1.2, 1.6, 2];
export const DK_TICKS = [-0.6, -0.3, -0.1, 0, 0.1, 0.3, 0.6];

export type Rgb = [number, number, number];

export function lutRgb(lut: Uint8Array, index: number): Rgb {
  const i = Math.max(0, Math.min(255, Math.round(index))) * 3;
  return [lut[i], lut[i + 1], lut[i + 2]];
}

/** LUT index of a value on [lo, hi], saturating at the ends. */
export function lutIndex(value: number, [lo, hi]: readonly [number, number]): number {
  const t = (value - lo) / (hi - lo);
  return Math.round(Math.max(0, Math.min(1, t)) * 255);
}

export function kColor(k: number): Rgb {
  return lutRgb(SPEED_LUT, lutIndex(k, K_DOMAIN));
}

export function balanceColor(dk: number): Rgb {
  return lutRgb(BALANCE_LUT, lutIndex(dk, DK_DOMAIN));
}

/** CSS linear-gradient stops for legends (16 stops is visually exact). */
export function lutGradient(lut: Uint8Array, direction = "to right"): string {
  const stops = Array.from({ length: 17 }, (_, i) => {
    const [r, g, b] = lutRgb(lut, (i / 16) * 255);
    return `rgb(${r} ${g} ${b}) ${((i / 16) * 100).toFixed(2)}%`;
  });
  return `linear-gradient(${direction}, ${stops.join(", ")})`;
}

/** Lawson classes A..E sample cmocean speed at 0.1/0.3/0.5/0.7/0.9 (design-system §2.5). */
export const LAWSON_COLORS: Rgb[] = [0.1, 0.3, 0.5, 0.7, 0.9].map((t) => lutRgb(SPEED_LUT, t * 255));
