import { describe, expect, it } from "vitest";
import { parseAxis, parseCoordPair, parseCoords } from "@/components/location/CoordinateForm/CoordinateForm.utils";

describe("parseCoords", () => {
  it("accepts comma and dot decimals", () => {
    expect(parseCoords("4,5", "-74.25")).toEqual({ lat: 4.5, lon: -74.25 });
  });
  it("rejects out-of-range or empty values", () => {
    expect(parseCoords("91", "0")).toBeNull();
    expect(parseCoords("0", "181")).toBeNull();
    expect(parseCoords("", "1")).toBeNull();
  });
  it("accepts DMS and DDM in either field", () => {
    const c = parseCoords(`5°32'13"N`, `73°21'38"W`);
    expect(c?.lat).toBeCloseTo(5.536944, 5);
    expect(c?.lon).toBeCloseTo(-73.360556, 5);
  });
  it("rejects a hemisphere on the wrong axis", () => {
    expect(parseCoords("5 N", "73 N")).toBeNull();
    expect(parseCoords("5 E", "73 W")).toBeNull();
  });
});

describe("parseAxis", () => {
  it("reads decimal degrees with optional hemisphere letters", () => {
    expect(parseAxis("5.5", "lat")).toBe(5.5);
    expect(parseAxis("5,5 S", "lat")).toBe(-5.5);
    expect(parseAxis("N 5.5", "lat")).toBe(5.5);
    expect(parseAxis("73.25 W", "lon")).toBe(-73.25);
  });
  it("reads degrees, decimal minutes (DDM)", () => {
    expect(parseAxis("5 32.2 N", "lat")).toBeCloseTo(5 + 32.2 / 60, 8);
    expect(parseAxis("5°32,2'N", "lat")).toBeCloseTo(5 + 32.2 / 60, 8);
  });
  it("reads degrees, minutes, seconds with typographic marks", () => {
    expect(parseAxis(`5°32′13″N`, "lat")).toBeCloseTo(5 + 32 / 60 + 13 / 3600, 8);
    expect(parseAxis("5 32 13,5 N", "lat")).toBeCloseTo(5 + 32 / 60 + 13.5 / 3600, 8);
  });
  it("treats O and W as west and S as south", () => {
    expect(parseAxis(`73°21'38"O`, "lon")).toBeCloseTo(-73.360556, 5);
    expect(parseAxis(`73°21'38"w`, "lon")).toBeCloseTo(-73.360556, 5);
    expect(parseAxis("10 s", "lat")).toBe(-10);
    expect(parseAxis("10 E", "lon")).toBe(10);
  });
  it("rejects minutes or seconds of 60 or more and conflicting signs", () => {
    expect(parseAxis("5 60 N", "lat")).toBeNull();
    expect(parseAxis("5 30 60 N", "lat")).toBeNull();
    expect(parseAxis("-5 N", "lat")).toBeNull();
    expect(parseAxis("N 5 N", "lat")).toBeNull();
    expect(parseAxis("5.5 30", "lat")).toBeNull();
    expect(parseAxis("abc", "lat")).toBeNull();
    expect(parseAxis("", "lat")).toBeNull();
  });
  it("requires a mark or a space between degrees, minutes and seconds", () => {
    // Run-together digits must not be guessed into 5°32'13" or 5°3'0".
    expect(parseAxis(`5°3213"N`, "lat")).toBeNull();
    expect(parseAxis(`5° 30"`, "lat")).toBeNull();
    expect(parseAxis(`5°32'13"`, "lat")).toBeCloseTo(5 + 32 / 60 + 13 / 3600, 8);
    expect(parseAxis("5°32", "lat")).toBeCloseTo(5 + 32 / 60, 8);
  });
  it("keeps 59.9999 seconds below the next minute", () => {
    expect(parseAxis(`5°32'59.9999"N`, "lat")).toBeCloseTo(5 + 32 / 60 + 59.9999 / 3600, 10);
  });
});

describe("parseCoordPair", () => {
  it("splits a pasted DMS pair by hemisphere letters", () => {
    const c = parseCoordPair(`5°32'13"N 73°21'38"W`);
    expect(c?.lat).toBeCloseTo(5.536944, 5);
    expect(c?.lon).toBeCloseTo(-73.360556, 5);
  });
  it("accepts longitude first and semicolon or comma separators", () => {
    expect(parseCoordPair("73.5 W, 5.25 N")).toEqual({ lat: 5.25, lon: -73.5 });
    expect(parseCoordPair("4,5; -74,25")).toEqual({ lat: 4.5, lon: -74.25 });
    expect(parseCoordPair("4.5, -74.25")).toEqual({ lat: 4.5, lon: -74.25 });
  });
  it("splits pairs whose hemisphere letters come first", () => {
    const c = parseCoordPair(`N 5°32'13" O 73°21'38"`);
    expect(c?.lat).toBeCloseTo(5.536944, 5);
    expect(c?.lon).toBeCloseTo(-73.360556, 5);
    expect(parseCoordPair("S4.5 W74.25")).toEqual({ lat: -4.5, lon: -74.25 });
    expect(parseCoordPair("N 4,5, O 74,25")).toEqual({ lat: 4.5, lon: -74.25 });
  });
  it("accepts a dot-decimal pair separated by a bare comma", () => {
    expect(parseCoordPair("4.60976,-74.08175")).toEqual({ lat: 4.60976, lon: -74.08175 });
  });
  it("returns null for a single value", () => {
    expect(parseCoordPair("4.5")).toBeNull();
  });
});
