import { describe, expect, it } from "vitest";
import { toDms } from "@/lib/format/format.coordinate";

describe("toDms", () => {
  it("formats with hemisphere letter, O for west", () => {
    expect(toDms(5.536944, "lat")).toBe(`5°32′13″ N`);
    expect(toDms(-73.360556, "lon")).toBe(`73°21′38″ O`);
    expect(toDms(-4.5, "lat")).toBe(`4°30′00″ S`);
  });
  it("carries rounded seconds into minutes and degrees", () => {
    expect(toDms(4.999999, "lat")).toBe(`5°00′00″ N`);
  });
  it("uses N/E for values that round to zero", () => {
    expect(toDms(-0.0000001, "lat")).toBe(`0°00′00″ N`);
    expect(toDms(-0.0000001, "lon")).toBe(`0°00′00″ E`);
  });
  it("shows a dash without a value", () => {
    expect(toDms(null, "lat")).toBe("—");
  });
});
