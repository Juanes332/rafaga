import { describe, expect, it } from "vitest";
import { readoutText, scaleBar } from "@/components/results/FlowCanvas/FlowCanvas.utils";
import { i18n } from "@/lib/i18n/i18n";

describe("FlowCanvas utils", () => {
  it("formats the hover readout 'K 1,34 — 5,1 m/s'", () => {
    expect(readoutText(1.3412, 5.14, i18n.t)?.replace(/\u2009/g, " ")).toBe("K 1,34 — 5,1 m/s");
  });
  it("hides the readout over solids", () => {
    expect(readoutText(Number.NaN, 2, i18n.t)).toBeNull();
  });
  it("omits speed when the field is missing", () => {
    expect(readoutText(0.5, null, i18n.t)).toBe("K 0,50");
  });
  it("picks a round scale bar near 100 px", () => {
    expect(scaleBar(5, 1)).toEqual({ metres: 20, px: 100 });
    expect(scaleBar(1.3, 1)).toEqual({ metres: 50, px: 65 });
  });
});
