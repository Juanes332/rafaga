import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { KNOWN_WARNINGS } from "@/components/results/ResultInspector/ResultInspector.hook";
import results from "@/locales/es-CO/results.json";

const REPO = path.resolve(__dirname, "../../../../../..");
const labels = results.warnings as Record<string, string>;

function pyFiles(dir: string): string[] {
  if (!existsSync(dir)) return [];
  return readdirSync(dir).flatMap((n) => {
    const f = path.join(dir, n);
    return statSync(f).isDirectory() ? pyFiles(f) : f.endsWith(".py") ? [f] : [];
  });
}

/** Every warning code the solver or the scene compiler can emit, read from source. */
function emittedCodes(): string[] {
  const found = new Set<string>();
  for (const dir of ["services/solver/app", "services/api/app/services/scene"]) {
    for (const f of pyFiles(path.join(REPO, dir))) {
      for (const m of readFileSync(f, "utf8").matchAll(/["']code["']\s*:\s*["']([a-z0-9_]+)["']/g)) found.add(m[1]);
    }
  }
  const schema = path.join(REPO, "docs/architecture/contracts/scene.schema.json");
  if (existsSync(schema)) {
    const enumValues = JSON.parse(readFileSync(schema, "utf8")).properties.warnings.items.properties.code.enum as string[];
    enumValues.forEach((c) => found.add(c));
  }
  return [...found].filter((c) => !["job_failed"].includes(c));
}

describe("solver warning labels (BL-12)", () => {
  it("finds the codes in the sources it scans", () => {
    const codes = emittedCodes();
    expect(codes).toEqual(expect.arrayContaining(["domain_top_capped", "low_reynolds", "below_analysis_height", "setback_tiers_truncated"]));
  });

  it("has an es-CO label for every emitted warning code", () => {
    const missing = emittedCodes().filter((c) => !labels[c] || labels[c].trim() === "");
    expect(missing).toEqual([]);
  });

  it("shows every labelled code in the inspector", () => {
    const unlisted = Object.keys(labels).filter((k) => k !== "title" && !(KNOWN_WARNINGS as readonly string[]).includes(k));
    expect(unlisted).toEqual([]);
    expect(labels.domain_top_capped).toBe("El dominio 3D se recortó por memoria; los edificios muy altos pueden tener menos precisión.");
  });
});
