/** Potential flow past a cylinder of radius r at the origin, unit free stream along +x. */
export function cylinderVelocity(x: number, y: number, r: number): [number, number] {
  const r2 = x * x + y * y;
  if (r2 < 1e-12) return [0, 0];
  const k = (r * r) / (r2 * r2);
  return [1 - k * (x * x - y * y), -2 * k * x * y];
}

interface StreamlineOptions {
  width: number;
  height: number;
  lines: number;
  /** Obstacle radius as a fraction of the height. */
  radius?: number;
}

function trace(y0: number, w: number, r: number, step: number): string {
  let x = -w / 2;
  let y = y0;
  const pts: string[] = [];
  for (let i = 0; i < 2000 && x < w / 2; i += 1) {
    pts.push(`${(x + w / 2).toFixed(1)},${y.toFixed(1)}`);
    // Midpoint (RK2) keeps lines smooth around the obstacle.
    const [u1, v1] = cylinderVelocity(x, y, r);
    const [u2, v2] = cylinderVelocity(x + (u1 * step) / 2, y + (v1 * step) / 2, r);
    const n = Math.hypot(u2, v2) || 1;
    x += (u2 / n) * step;
    y += (v2 / n) * step;
  }
  return `M${pts.join("L")}`;
}

/** Decorative static streamlines (SVG path data), centred on the obstacle. */
export function cylinderStreamlines({ width, height, lines, radius = 0.12 }: StreamlineOptions): string[] {
  const r = height * radius;
  const gap = height / (lines + 1);
  return Array.from({ length: lines }, (_, i) => {
    // Seeds avoid y = 0 exactly, where the dividing streamline hits the stagnation point.
    const y0 = -height / 2 + gap * (i + 1) + gap * 0.07;
    return trace(y0, width, r, 4).replace(/,(-?[\d.]+)/g, (_m, yy: string) => `,${(Number(yy) + height / 2).toFixed(1)}`);
  });
}
