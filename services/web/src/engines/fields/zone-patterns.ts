export type ZoneKind = "acceleration" | "stagnation" | "reduction";

/** Pattern pitch in px (design-system §2.6). */
export const PATTERN_SIZE: Record<ZoneKind, number> = { acceleration: 6, stagnation: 6, reduction: 8 };

const mod = (a: number, n: number) => ((a % n) + n) % n;

/** Whether pixel (x, y) of a pattern tile is inked: hatch 45°, dots, or cross-hatch ±45°. */
export function patternHit(kind: ZoneKind, x: number, y: number): boolean {
  const n = PATTERN_SIZE[kind];
  if (kind === "acceleration") return mod(x + y, n) < 1.5;
  if (kind === "stagnation") return mod(x, n) < 1.5 && mod(y, n) < 1.5;
  return mod(x + y, n) < 1.5 || mod(x - y, n) < 1.5;
}

/** Canvas pattern tile drawn with the zone colour (browser only). */
export function patternTile(kind: ZoneKind, color: string): HTMLCanvasElement {
  const n = PATTERN_SIZE[kind];
  const c = document.createElement("canvas");
  c.width = c.height = n;
  const ctx = c.getContext("2d");
  if (!ctx) return c;
  ctx.fillStyle = color;
  for (let y = 0; y < n; y += 1) for (let x = 0; x < n; x += 1) if (patternHit(kind, x, y)) ctx.fillRect(x, y, 1, 1);
  return c;
}
