import { describe, expect, it } from "vitest";
import { describeDifferences } from "@/components/compare/DifferenceList/DifferenceList.utils";
import { i18n } from "@/lib/i18n/i18n";

describe("describeDifferences", () => {
  it("writes the design-system sentence for cell size and direction", () => {
    const text = describeDifferences(
      [
        { field: "dx", a: 1, b: 2 },
        { field: "direction", a: 90, b: 45 },
      ],
      i18n.t,
    );
    expect(text.replace(/\u2009/g, " ")).toBe(
      "Estos resultados no se pueden comparar porque tienen distinto tamaño de celda (1,0 m y 2,0 m) y distinta dirección (desde E · 90° y desde NE · 45°). Simula ambas alternativas con los mismos parámetros.",
    );
  });
  it("names the simulation kinds in plain words", () => {
    expect(describeDifferences([{ field: "kind", a: "plan2d", b: "section2d" }], i18n.t)).toContain("distinto tipo de simulación (planta 2D y corte vertical)");
  });
  it("joins three or more with commas and a final y", () => {
    const text = describeDifferences(
      [
        { field: "grid", a: null, b: null },
        { field: "z0", a: 0.5, b: 1 },
        { field: "section", a: null, b: null },
      ],
      i18n.t,
    ).replace(/\u2009/g, " ");
    expect(text).toContain("distinta malla de salida, distinta rugosidad del terreno (0,50 m y 1,00 m) y distinta línea de corte");
  });
});
