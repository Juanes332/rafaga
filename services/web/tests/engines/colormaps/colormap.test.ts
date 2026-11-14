import { describe, expect, it } from "vitest";
import { BALANCE_LUT, SPEED_LUT, balanceColor, kColor, lutRgb } from "@/engines/colormaps/colormap";

type Sample = [number, [number, number, number]];
// Reference samples from cmocean 3.0.3, cm(i/255); the solver PNGs use the same tables.
const SPEED: Sample[] = [
  [0, [255, 253, 205]],
  [64, [201, 186, 69]],
  [128, [95, 146, 12]],
  [191, [11, 96, 45]],
  [255, [23, 35, 19]],
];
const BALANCE: Sample[] = [
  [0, [24, 28, 67]],
  [64, [56, 136, 186]],
  [128, [241, 236, 235]],
  [191, [192, 90, 60]],
  [255, [60, 9, 18]],
];

describe("cmocean LUTs (WEB-04)", () => {
  it("have 256 RGB entries", () => {
    expect(SPEED_LUT.length).toBe(256 * 3);
    expect(BALANCE_LUT.length).toBe(256 * 3);
  });
  it.each(SPEED)("speed[%i] matches cmocean within 1/255", (i, rgb) => {
    lutRgb(SPEED_LUT, i).forEach((c, k) => expect(Math.abs(c - rgb[k])).toBeLessThanOrEqual(1));
  });
  it.each(BALANCE)("balance[%i] matches cmocean within 1/255", (i, rgb) => {
    lutRgb(BALANCE_LUT, i).forEach((c, k) => expect(Math.abs(c - rgb[k])).toBeLessThanOrEqual(1));
  });
  it("maps K on the fixed 0–2 domain and saturates above", () => {
    expect(kColor(0)).toEqual(lutRgb(SPEED_LUT, 0));
    expect(kColor(2)).toEqual(lutRgb(SPEED_LUT, 255));
    expect(kColor(3.4)).toEqual(lutRgb(SPEED_LUT, 255));
  });
  it("centres ΔK at 0 on the symmetric ±0.6 domain", () => {
    expect(balanceColor(0)).toEqual(lutRgb(BALANCE_LUT, 128));
    expect(balanceColor(-0.6)).toEqual(lutRgb(BALANCE_LUT, 0));
    expect(balanceColor(0.9)).toEqual(lutRgb(BALANCE_LUT, 255));
  });
});
