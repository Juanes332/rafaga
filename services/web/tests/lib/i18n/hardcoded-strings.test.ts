import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const ROOT = path.resolve(__dirname, "../../../src/components");
// Proper nouns and symbols that are the same in any locale.
const ALLOWED = new Set(["Ráfaga", "K", "ΔK", "N", "A", "B", "×", "—", "·", "%", "m", "°", "⇄", "PNG", "PDF", "GPU", "CPU", "3D", "2D"]);

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = path.join(dir, name);
    if (statSync(full).isDirectory()) return name === "ui" ? [] : walk(full);
    return full.endsWith(".tsx") ? [full] : [];
  });
}

/** JSX text nodes and user-facing attributes written as literals. */
function findHardcoded(source: string): string[] {
  const hits: string[] = [];
  // Text between tags; code characters are excluded so TS generics never match.
  const text = /(?<![=>]\s*)>\s*([^<>{}\n=();|&[\]]*[A-Za-zÁÉÍÓÚáéíóúñÑ]{2,}[^<>{}\n=();|&[\]]*?)\s*</g;
  const attrs = /\b(?:aria-label|placeholder|title|alt|label)="([^"]*[A-Za-zÁÉÍÓÚáéíóúñÑ]{2,}[^"]*)"/g;
  for (const re of [text, attrs]) {
    for (const m of source.matchAll(re)) {
      const value = m[1].trim();
      if (value && !ALLOWED.has(value)) hits.push(value);
    }
  }
  return hits;
}

describe("i18n coverage", () => {
  it("detects a hard-coded string in a fixture", () => {
    expect(findHardcoded("<p>Crear cuenta</p>")).toContain("Crear cuenta");
    expect(findHardcoded('<input aria-label="Buscar lugar" />')).toContain("Buscar lugar");
    expect(findHardcoded("<p>{t('auth:title')}</p>")).toEqual([]);
  });

  it("finds no hard-coded user-visible strings in components", () => {
    const offenders = walk(ROOT).flatMap((file) =>
      findHardcoded(readFileSync(file, "utf8")).map((s) => `${path.relative(ROOT, file)}: ${s}`),
    );
    expect(offenders).toEqual([]);
  });
});
