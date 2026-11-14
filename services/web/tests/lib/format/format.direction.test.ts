import { describe, expect, it } from "vitest";
import { degToCardinal, directionLabel, directionName, sectorIndex, windFromLabel } from "@/lib/format/format.direction";

describe("direction names", () => {
  it("names the 16 Spanish compass points", () => {
    expect(directionName(0)).toBe("N");
    expect(directionName(90)).toBe("E");
    expect(directionName(202.5)).toBe("SSO");
    expect(directionName(270)).toBe("O");
    expect(directionName(337.5)).toBe("NNO");
  });
  it("rounds to the nearest sector and wraps 360", () => {
    expect(sectorIndex(359)).toBe(0);
    expect(sectorIndex(11)).toBe(0);
    expect(sectorIndex(12)).toBe(1);
  });
  it("states the meteorological FROM convention with name and degrees", () => {
    expect(directionLabel(90)).toBe("desde E · 90°");
    expect(directionLabel(45)).toBe("desde NE · 45°");
    expect(directionLabel(22.5)).toBe("desde NNE · 22,5°");
    expect(windFromLabel(270)).toBe("desde O · 270°");
  });
});

describe("degToCardinal", () => {
  it("defaults to 16 points", () => {
    expect(degToCardinal(202.5)).toBe("SSO");
  });
  it("supports 8 and 4 points and wraps negatives and 360", () => {
    expect(degToCardinal(45, 8)).toBe("NE");
    expect(degToCardinal(100, 8)).toBe("E");
    expect(degToCardinal(315, 8)).toBe("NO");
    expect(degToCardinal(-90, 4)).toBe("O");
    expect(degToCardinal(360, 4)).toBe("N");
    expect(degToCardinal(44, 4)).toBe("N");
    expect(degToCardinal(46, 4)).toBe("E");
  });
  it("splits exactly on the 16-point sector boundaries", () => {
    expect(degToCardinal(348.75)).toBe("N");
    expect(degToCardinal(348.74)).toBe("NNO");
    expect(degToCardinal(11.25)).toBe("NNE");
    expect(degToCardinal(11.24)).toBe("N");
  });
  it("returns a dash for a missing bearing", () => {
    expect(degToCardinal(Number.NaN)).toBe("—");
  });
});

describe("windFromLabel normalisation", () => {
  it("wraps negative and near-360 bearings into 0..360", () => {
    expect(windFromLabel(-45)).toBe("desde NO · 315°");
    expect(windFromLabel(359.96)).toBe("desde N · 0°");
    expect(windFromLabel(720)).toBe("desde N · 0°");
  });
});
