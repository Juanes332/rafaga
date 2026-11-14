export interface CompassPoint {
  label: string;
  x: number;
  y: number;
  /** Cardinals (N, E, S, O) draw larger than the intercardinals. */
  major: boolean;
  north: boolean;
}

const POINTS = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"] as const;

/** Label positions around the centre; `rotationDeg` turns the whole rose clockwise. */
export function compassPoints(rotationDeg: number, radius: number): CompassPoint[] {
  return POINTS.map((label, i) => {
    const a = ((i * 45 + rotationDeg) * Math.PI) / 180;
    return { label, x: Math.sin(a) * radius, y: -Math.cos(a) * radius, major: i % 2 === 0, north: i === 0 };
  });
}
