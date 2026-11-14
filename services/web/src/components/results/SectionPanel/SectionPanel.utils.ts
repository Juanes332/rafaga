type P = [number, number];

/** Flow vector (towards) for a meteorological "from" bearing: wind from E flows to −x. */
export function flowVector(fromDeg: number): P {
  const r = (fromDeg * Math.PI) / 180;
  return [-Math.sin(r), -Math.cos(r)];
}

/** True when the line p0 → p1 runs with the wind (p0 on the upwind side). */
export function runsDownwind(p0: P, p1: P, fromDeg: number): boolean {
  const [fx, fy] = flowVector(fromDeg);
  return (p1[0] - p0[0]) * fx + (p1[1] - p0[1]) * fy > 0;
}

export function sectionLength(p0: P, p1: P): number {
  return Math.hypot(p1[0] - p0[0], p1[1] - p0[1]);
}
