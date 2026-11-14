type Px = [number, number];

/** Scale of a traced plan from two picked image points and the real distance between them. */
export function metresPerPixel(p1: Px, p2: Px, distanceM: number): number | null {
  const px = Math.hypot(p2[0] - p1[0], p2[1] - p1[1]);
  if (px < 1e-6 || !(distanceM > 0)) return null;
  return distanceM / px;
}

/** Ruler reading between two image points under a calibration. */
export function measureMetres(a: Px, b: Px, mpp: number): number {
  return Math.hypot(b[0] - a[0], b[1] - a[1]) * mpp;
}

export function relativeError(measured: number, expected: number): number {
  return Math.abs(measured - expected) / Math.abs(expected);
}
