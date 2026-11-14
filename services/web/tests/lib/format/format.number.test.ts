import { describe, expect, it } from "vitest";
import { formatArea, formatCoord, formatNumber, formatPercent, formatUnit, THIN } from "@/lib/format/format.number";

describe("es-CO number formatting", () => {
  it("uses a decimal comma and a dot for thousands", () => {
    expect(formatNumber(0.7412, 2)).toBe("0,74");
    expect(formatNumber(1020, 0)).toBe("1.020");
  });
  it("puts a thin space between number and unit", () => {
    expect(formatUnit(5.14, 1, "m/s")).toBe(`5,1${THIN}m/s`);
  });
  it("formats percentages from a fraction with one decimal", () => {
    expect(formatPercent(0.061)).toBe(`6,1${THIN}%`);
    expect(formatPercent(0.4, 0)).toBe(`40${THIN}%`);
  });
  it("formats areas as whole square metres", () => {
    expect(formatArea(1020.4)).toBe(`1.020${THIN}m²`);
  });
  it("formats coordinates with five decimals", () => {
    expect(formatCoord(12.3456789)).toBe("12,34568");
  });
  it("renders missing values as an em dash", () => {
    expect(formatNumber(null, 2)).toBe("—");
    expect(formatNumber(Number.NaN, 2)).toBe("—");
  });
});
