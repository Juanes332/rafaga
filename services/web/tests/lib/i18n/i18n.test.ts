import { describe, expect, it } from "vitest";
import { i18n, initI18n } from "@/lib/i18n/i18n";

describe("i18n", () => {
  it("loads es-CO namespaces from locales", () => {
    initI18n();
    expect(i18n.language).toBe("es-CO");
    expect(i18n.t("common:disclaimer")).toBe(
      "Herramienta de anteproyecto: compara alternativas, no sustituye un ensayo en túnel de viento.",
    );
  });
});
