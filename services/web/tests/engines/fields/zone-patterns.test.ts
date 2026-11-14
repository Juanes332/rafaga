import { describe, expect, it } from "vitest";
import { patternHit, PATTERN_SIZE } from "@/engines/fields/zone-patterns";

describe("zone patterns (never colour alone)", () => {
  it("uses a 6 px diagonal hatch for acceleration", () => {
    expect(PATTERN_SIZE.acceleration).toBe(6);
    expect(patternHit("acceleration", 0, 0)).toBe(true);
    expect(patternHit("acceleration", 3, 0)).toBe(false);
    expect(patternHit("acceleration", 5, 1)).toBe(true);
  });
  it("uses 1.5 px dots on a 6 px pitch for stagnation", () => {
    expect(patternHit("stagnation", 0, 0)).toBe(true);
    expect(patternHit("stagnation", 3, 3)).toBe(false);
  });
  it("uses a ±45° cross-hatch on an 8 px pitch for reduction", () => {
    expect(PATTERN_SIZE.reduction).toBe(8);
    expect(patternHit("reduction", 0, 0)).toBe(true);
    expect(patternHit("reduction", 3, 5)).toBe(true);
    expect(patternHit("reduction", 4, 0)).toBe(false);
  });
});
