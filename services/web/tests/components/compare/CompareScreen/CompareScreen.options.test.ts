import { describe, expect, it } from "vitest";
import { defaultPair, type CompareOption } from "@/components/compare/CompareScreen/CompareScreen.options";

const opt = (resultId: string, alternativeId: string, direction = 90): CompareOption => ({
  resultId, studyId: `s-${resultId}`, alternativeId, label: resultId, name: alternativeId, direction, kind: "plan2d",
});

describe("defaultPair", () => {
  it("puts the base as A and an alternative in the same direction as B (BL-12: alternative vs base)", () => {
    const options = [opt("r1", "alt-1"), opt("r2", "alt-2"), opt("r3", "base")];
    expect(defaultPair(options, "base")).toEqual(["r3", "r1"]);
  });

  it("never pairs the base with another result of the base", () => {
    const options = [opt("r1", "base", 0), opt("r2", "base", 90), opt("r3", "alt-1", 90)];
    expect(defaultPair(options, "base")).toEqual(["r2", "r3"]);
  });

  it("falls back to the first two results of one direction without a simulated base", () => {
    const options = [opt("r1", "alt-1"), opt("r2", "alt-2")];
    expect(defaultPair(options, "base")).toEqual(["r1", "r2"]);
    expect(defaultPair(options)).toEqual(["r1", "r2"]);
    expect(defaultPair([opt("r1", "alt-1")])).toBeNull();
  });
});
