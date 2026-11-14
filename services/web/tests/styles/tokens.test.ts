import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const css = readFileSync(path.resolve(__dirname, "../../src/styles/tokens.css"), "utf8");

function block(selector: string): Record<string, string> {
  const start = css.indexOf(selector);
  const body = css.slice(css.indexOf("{", start) + 1, css.indexOf("}", start));
  return Object.fromEntries([...body.matchAll(/--([\w-]+):\s*(#[0-9a-f]{6})/gi)].map((m) => [m[1], m[2].toLowerCase()]));
}

function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

const light = block(':root[data-theme="light"]');
const dark = block(':root[data-theme="dark"]');
const TEXT = ["ink", "ink-muted", "accent", "zone-stagnation", "zone-reduction", "danger"];

describe("design tokens (WEB-02)", () => {
  it("define the contract values", () => {
    expect(light["color-ground"]).toBe("#e8eceb");
    expect(light["color-accent"]).toBe("#2b4fd8");
    expect(dark["color-ground"]).toBe("#172126");
    expect(dark["color-accent"]).toBe("#7f98ff");
  });

  it.each([
    ["light", light],
    ["dark", dark],
  ])("text tokens reach 4.5:1 on every surface (%s)", (_name, t) => {
    for (const fg of [...TEXT, "zone-accel-text"]) {
      for (const bg of ["color-ground", "color-surface", "color-surface-raised"]) {
        expect(contrast(t[`color-${fg}`], t[bg]), `${fg} on ${bg}`).toBeGreaterThanOrEqual(4.5);
      }
    }
  });

  it.each([
    ["light", light],
    ["dark", dark],
  ])("control borders reach 3:1 where controls live (%s)", (_name, t) => {
    expect(contrast(t["color-control-border"], t["color-ground"])).toBeGreaterThanOrEqual(3);
    expect(contrast(t["color-control-border"], t["color-surface-raised"])).toBeGreaterThanOrEqual(3);
  });

  it("accent ink reads on the accent in both themes", () => {
    expect(contrast(light["color-accent-ink"], light["color-accent"])).toBeGreaterThanOrEqual(4.5);
    expect(contrast(dark["color-accent-ink"], dark["color-accent"])).toBeGreaterThanOrEqual(4.5);
  });

  it("keeps the OS-dark block identical to the explicit dark theme", () => {
    const os = block(':root:not([data-theme="light"])');
    expect(os).toEqual(dark);
  });
});
