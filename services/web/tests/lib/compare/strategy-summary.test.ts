import { describe, expect, it } from "vitest";
import { GOLDEN } from "./strategy-summary.golden";
import { signedPct, summarizeStrategy, summaryLines, VERDICT_THRESHOLD_PCT } from "@/lib/compare/strategy-summary";
import { formatArea, formatNumber } from "@/lib/format/format.number";

const fn = (lines: string[]) => lines.map((l) => l.replace(/\s+/g, " "));

describe("summarizeStrategy", () => {
  it("uses a 3 % threshold on the mean change", () => {
    expect(VERDICT_THRESHOLD_PCT).toBe(3);
    const base = [1, 1, 1, 1];
    const mk = (v: number) => summarizeStrategy({ ...GOLDEN.input, ka: base, kb: base.map(() => v), dkReduction: -0.5 });
    expect(mk(0.96).verdict).toBe("improves");
    expect(mk(1.04).verdict).toBe("worsens");
    expect(mk(0.98).verdict).toBe("neutral");
    expect(mk(1.02).verdict).toBe("neutral");
  });

  it("measures the protected zone only on cells with dK below the threshold", () => {
    const s = summarizeStrategy({ ...GOLDEN.input, ka: [1, 1, 1, 1], kb: [0.5, 0.5, 1, 1], dkReduction: -0.1 });
    expect(s.protectedPct).toBeCloseTo(-50, 6);
    expect(s.overallPct).toBeCloseTo(-25, 6);
  });

  it("ignores cells that are not fluid in both fields", () => {
    const s = summarizeStrategy({ ...GOLDEN.input, ka: [1, Number.NaN, 1], kb: [0.9, 5, Number.NaN], dkReduction: -0.5 });
    expect(s.overallPct).toBeCloseTo(-10, 6);
    expect(s.protectedPct).toBeNull();
  });

  it("derives class shifts and bounds on improved and worsened area", () => {
    const s = summarizeStrategy(GOLDEN.input);
    expect(s.shift).toEqual({ from: "C", to: "B", m2: 320 });
    expect(s.improvedM2).toBe(320);
    expect(s.worsenedM2).toBe(0);
  });

  it("has no Lawson part without comfort", () => {
    const s = summarizeStrategy({ ...GOLDEN.input, comfort: undefined });
    expect(s.shift).toBeNull();
    expect(s.unsafe).toBeNull();
  });
});

describe("summaryLines (Spanish, shared golden with the PDF)", () => {
  it("writes the golden sentences", () => {
    expect(fn(summaryLines(summarizeStrategy(GOLDEN.input)))).toEqual(GOLDEN.sentences);
  });

  it("says the whole area when nothing is protected, and never calls a 1 % change an effect", () => {
    const calm = summarizeStrategy({ ...GOLDEN.input, ka: [1, 1], kb: [1.01, 0.99], comfort: undefined });
    const lines = summaryLines(calm);
    expect(lines.join(" ")).toContain("casi no cambia el viento");
    expect(lines.join(" ")).toContain("Veredicto: sin cambio relevante");
  });
});

describe("rounding parity with report_summary.py", () => {
  it("rounds half away from zero, as the solver test_rounding_matches_the_web_half_away_from_zero asserts", () => {
    expect([formatNumber(2.5, 0), formatNumber(12.5, 0), formatNumber(1005, 0)]).toEqual(["3", "13", "1.005"]);
    expect(formatArea(1500.5).replace(/\s+/g, " ")).toBe("1.501 m²");
    expect([signedPct(0.25), signedPct(-0.25), signedPct(1.05)]).toEqual(["+0,3 %", "−0,3 %", "+1,1 %"]);
  });
});
